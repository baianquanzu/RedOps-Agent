"""
RedOps - 渗透测试任务编排器
实现完整的渗透测试工作流程
"""

import os
import re
import json
import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime


class ScanTask:
    """扫描任务"""
    def __init__(self, target: str, task_id: str = None):
        self.task_id = task_id or f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.target = target
        self.status = "pending"
        self.results = {
            "domain": None,
            "info_gathered": [],
            "urls": [],
            "subdomains": [],
            "directories": [],
            "ports": {},
            "frameworks": {},
            "vulnerabilities": [],
            "creds_found": []
        }
        self.logs = []
        self.start_time = None
        self.end_time = None
    
    def add_log(self, level: str, message: str):
        log = {
            "time": datetime.now().isoformat(),
            "level": level,
            "message": message
        }
        self.logs.append(log)
        return log


class ReconOrchestrator:
    """渗透测试任务编排器"""
    
    def __init__(self, executor, workspace: str = "/tmp/redops"):
        self.executor = executor
        self.workspace = workspace
        self.current_task: Optional[ScanTask] = None
        self.callback: Optional[Callable] = None
        os.makedirs(workspace, exist_ok=True)
    
    def set_callback(self, callback: Callable):
        self.callback = callback
    
    async def send_update(self, level: str, message: str):
        if self.current_task:
            self.current_task.add_log(level, message)
        if self.callback:
            await self.callback(level, message)
    
    async def run_full_scan(self, target: str, config: Dict = None) -> Dict[str, Any]:
        """运行完整渗透测试"""
        task = ScanTask(target)
        self.current_task = task
        task.status = "running"
        task.start_time = datetime.now()
        config = config or {}
        
        try:
            # 阶段1: 信息搜集
            await self.send_update("info", f"[1/9] 开始信息搜集: {target}")
            domain = self._extract_domain(target)
            task.results["domain"] = domain
            
            # 阶段2: 子域名搜集
            await self.send_update("info", "[2/9] 搜集子域名...")
            subdomains = await self._gather_subdomains(domain, config)
            task.results["subdomains"] = subdomains
            await self.send_update("success", f"发现 {len(subdomains)} 个子域名")
            
            # 阶段3: URL搜集
            await self.send_update("info", "[3/9] 搜集URL...")
            urls = await self._gather_urls(domain, config)
            task.results["urls"] = urls
            await self.send_update("success", f"发现 {len(urls)} 个URL")
            
            # 阶段4: 目录扫描
            await self.send_update("info", "[4/9] 扫描目录...")
            directories = await self._scan_directories(domain, config)
            task.results["directories"] = directories
            await self.send_update("success", f"发现 {len(directories)} 个目录")
            
            # 阶段5: 合并去重
            await self.send_update("info", "[5/9] 合并去重...")
            all_targets = self._merge_and_deduplicate(task.results)
            await self.send_update("success", f"合并后共 {len(all_targets)} 个目标")
            
            # 阶段6: 端口扫描
            await self.send_update("info", "[6/9] 扫描端口...")
            ports = await self._scan_ports(domain, config)
            task.results["ports"] = ports
            await self.send_update("success", f"发现 {len(ports)} 个开放端口")
            
            # 阶段7: 框架识别
            await self.send_update("info", "[7/9] 识别框架...")
            frameworks = await self._detect_frameworks(all_targets, config)
            task.results["frameworks"] = frameworks
            await self.send_update("success", f"识别到 {len(frameworks)} 种框架")
            
            # 阶段8: 漏洞扫描
            await self.send_update("info", "[8/9] 漏洞扫描...")
            vulns = await self._scan_vulnerabilities(all_targets, config)
            task.results["vulnerabilities"] = vulns
            await self.send_update("success", f"发现 {len(vulns)} 个漏洞")
            
            # 阶段9: 弱口令检测
            await self.send_update("info", "[9/9] 弱口令检测...")
            creds = await self._check_weak_passwords(ports, config)
            task.results["creds_found"] = creds
            if creds:
                await self.send_update("warning", f"发现 {len(creds)} 组弱口令!")
            else:
                await self.send_update("success", "未发现弱口令")
            
            task.status = "completed"
            task.end_time = datetime.now()
            await self.send_update("success", "\n========== 扫描完成 ==========")
            await self._generate_report(task)
            
        except Exception as e:
            task.status = "failed"
            await self.send_update("error", f"错误: {str(e)}")
        
        return {"success": task.status == "completed", "task": task, "results": task.results, "logs": task.logs}
    
    def _extract_domain(self, target: str) -> str:
        match = re.search(r'https?://([^/]+)', target)
        return match.group(1) if match else target
    
    async def _gather_subdomains(self, domain: str, config: Dict) -> List[str]:
        subdomains = []
        
        # subfinder
        result = self.executor.execute(f"subfinder -d {domain}", timeout=120)
        if result.get("success"):
            found = [line.strip() for line in result.get("stdout", "").split('\n') if line.strip()]
            subdomains.extend(found)
            await self.send_update("info", f"  - Subfinder: {len(found)} 个")
        
        # assetfinder
        result = self.executor.execute(f"assetfinder {domain}", timeout=60)
        if result.get("success"):
            found = [line.strip() for line in result.get("stdout", "").split('\n') if line.strip()]
            subdomains.extend(found)
            await self.send_update("info", f"  - Assetfinder: {len(found)} 个")
        
        return list(set(subdomains))
    
    async def _gather_urls(self, domain: str, config: Dict) -> List[str]:
        urls = []
        
        # gau
        result = self.executor.execute(f"gau {domain}", timeout=180)
        if result.get("success"):
            found = [line.strip() for line in result.get("stdout", "").split('\n') if line.strip()]
            urls.extend(found[:500])
            await self.send_update("info", f"  - GAU: {len(found[:500])} 个URL")
        
        # waybackurls
        result = self.executor.execute(f"echo {domain} | waybackurls", timeout=120)
        if result.get("success"):
            found = [line.strip() for line in result.get("stdout", "").split('\n') if line.strip()]
            urls.extend(found[:200])
            await self.send_update("info", f"  - Waybackurls: {len(found[:200])} 个URL")
        
        # FOFA
        fofa_api = config.get("fofa_api")
        if fofa_api:
            fofa_results = await self._search_fofa(domain, fofa_api)
            urls.extend(fofa_results)
            await self.send_update("info", f"  - FOFA: {len(fofa_results)} 个URL")
        
        return list(set(urls))
    
    async def _search_fofa(self, domain: str, api_key: str) -> List[str]:
        urls = []
        try:
            import base64
            query = f'domain="{domain}"'
            query_b64 = base64.b64encode(query.encode()).decode()
            result = self.executor.execute(
                f'curl -s "https://fofa.info/api/v1/search/all?key={api_key}&qbase64={query_b64}&size=100"',
                timeout=30
            )
            if result.get("success"):
                try:
                    data = json.loads(result.get("stdout", ""))
                    if data.get("results"):
                        for item in data["results"]:
                            if item:
                                urls.append(str(item[0]))
                except:
                    pass
        except Exception as e:
            await self.send_update("warning", f"FOFA搜索失败")
        return urls
    
    async def _scan_directories(self, domain: str, config: Dict) -> List[str]:
        directories = []
        targets = [f"http://{domain}", f"https://{domain}"]
        
        for target in targets:
            # dirsearch
            output = os.path.join(self.workspace, f"dirsearch_{domain.replace('.', '_')}.txt")
            result = self.executor.execute(f"dirsearch -u {target} -o {output} --format plain", timeout=300)
            if os.path.exists(output):
                with open(output, 'r') as f:
                    for line in f:
                        if any(x in line for x in ['200', '301', '302', '403']):
                            directories.append(line.strip())
                await self.send_update("info", f"  - Dirsearch: {len(directories)} 个")
            
            # ffuf
            output2 = os.path.join(self.workspace, f"ffuf_{domain.replace('.', '_')}.txt")
            wordlist = "/usr/share/wordlists/dirb/common.txt"
            result = self.executor.execute(f"ffuf -u {target}/FUZZ -w {wordlist} -o {output2}", timeout=300)
            if os.path.exists(output2):
                await self.send_update("info", f"  - FFUF扫描完成")
        
        return list(set(directories))
    
    def _merge_and_deduplicate(self, results: Dict) -> List[str]:
        all_targets = set()
        if results.get("domain"):
            all_targets.add(f"http://{results['domain']}")
            all_targets.add(f"https://{results['domain']}")
        for subdomain in results.get("subdomains", []):
            if not subdomain.startswith("http"):
                subdomain = f"http://{subdomain}"
            all_targets.add(subdomain)
        all_targets.update(results.get("urls", []))
        all_targets.update(results.get("directories", []))
        return list(all_targets)
    
    async def _scan_ports(self, domain: str, config: Dict) -> Dict:
        ports = {}
        ports_config = config.get("ports", "1-1000")
        output = os.path.join(self.workspace, f"nmap_{domain.replace('.', '_')}.xml")
        result = self.executor.execute(f"nmap -sV -p {ports_config} {domain} -oX {output}", timeout=300)
        
        if os.path.exists(output):
            try:
                import xml.etree.ElementTree as ET
                tree = ET.parse(output)
                for port in tree.findall('.//port'):
                    state = port.find('state')
                    if state is not None and state.get('state') == 'open':
                        port_id = port.get('portid')
                        service = port.find('service')
                        ports[port_id] = {
                            "state": "open",
                            "service": service.get('name') if service is not None else "unknown",
                            "version": service.get('version') if service is not None else ""
                        }
                        await self.send_update("info", f"  - 端口 {port_id}: {ports[port_id]['service']}")
            except:
                pass
        return ports
    
    async def _detect_frameworks(self, targets: List[str], config: Dict) -> Dict:
        frameworks = {}
        framework_patterns = {
            "WordPress": ["wp-content", "wp-includes", "wordpress"],
            "Joomla": ["joomla", "com_content"],
            "Drupal": ["drupal", "sites/default"],
            "Spring": ["spring", " thymeleaf"],
            "Django": ["csrfmiddlewaretoken", "django"],
            "Flask": ["flask", "jinja"],
            "Laravel": ["laravel", "X-CSRF-TOKEN"],
            "Tomcat": ["apache-tomcat", "manager/html"],
            "Struts": ["struts", "action"],
            "Express": ["express", "node_modules"]
        }
        
        for target in targets[:30]:
            result = self.executor.execute(f"curl -s {target} | head -50", timeout=10)
            if result.get("success"):
                content = result.get("stdout", "").lower()
                for fw, patterns in framework_patterns.items():
                    if any(p in content for p in patterns):
                        if fw not in frameworks:
                            frameworks[fw] = []
                        if target not in frameworks[fw]:
                            frameworks[fw].append(target)
        
        return frameworks
    
    async def _scan_vulnerabilities(self, targets: List[str], config: Dict) -> List[Dict]:
        vulns = []
        severity = config.get("severity", "critical,high,medium")
        
        for target in targets[:30]:
            await self.send_update("info", f"  扫描: {target}")
            output = os.path.join(self.workspace, f"nuclei_{datetime.now().strftime('%H%M%S')}.json")
            result = self.executor.execute(f"nuclei -u {target} -severity {severity} -o {output} -json-export", timeout=300)
            
            if os.path.exists(output):
                with open(output, 'r') as f:
                    for line in f:
                        try:
                            vuln = json.loads(line.strip())
                            vuln["target"] = target
                            vulns.append(vuln)
                            await self.send_update("warning", f"  [!] {vuln.get('info', {}).get('name', 'Unknown')}")
                        except:
                            pass
        
        return vulns
    
    async def _check_weak_passwords(self, ports: Dict, config: Dict) -> List[Dict]:
        creds = []
        
        common_users = "/usr/share/wordlists/metasploit/default_users.txt"
        common_pass = "/usr/share/wordlists/metasploit/default_pass.txt"
        
        for port_id, info in ports.items():
            service = info.get("service", "").lower()
            if service in ["ssh", "ftp", "telnet", "smb"]:
                await self.send_update("info", f"  - 尝试{service}弱口令...")
                output = os.path.join(self.workspace, f"hydra_{port_id}.txt")
                result = self.executor.execute(
                    f"hydra -L {common_users} -P {common_pass} {self.current_task.target} {service} -V -o {output}",
                    timeout=600
                )
                if os.path.exists(output):
                    with open(output, 'r') as f:
                        for line in f:
                            if "login:" in line and "password:" in line:
                                m = re.search(r'login:\s*(\S+)\s*password:\s*(\S+)', line)
                                if m:
                                    creds.append({"service": service, "port": port_id, "user": m.group(1), "pass": m.group(2)})
                                    await self.send_update("warning", f"  [!] 发现: {m.group(1)}:{m.group(2)}")
        
        return creds
    
    async def _generate_report(self, task: ScanTask):
        report = f"""
========== RedOps 渗透测试报告 ==========

目标: {task.target}
时间: {task.start_time.strftime('%Y-%m-%d %H:%M:%S')}

【子域名】 ({len(task.results.get('subdomains', []))})
"""
        for sub in task.results.get('subdomains', [])[:20]:
            report += f"  - {sub}\n"
        
        report += f"\n【URL】 ({len(task.results.get('urls', []))})\n"
        for url in task.results.get('urls', [])[:30]:
            report += f"  - {url}\n"
        
        report += f"\n【端口】 ({len(task.results.get('ports', {}))})\n"
        for port, info in task.results.get('ports', {}).items():
            report += f"  - {port}/tcp: {info.get('service')} {info.get('version')}\n"
        
        report += f"\n【漏洞】 ({len(task.results.get('vulnerabilities', []))})\n"
        for vuln in task.results.get('vulnerabilities', [])[:20]:
            report += f"  - {vuln.get('info', {}).get('name', 'Unknown')}\n"
        
        report += f"\n【弱口令】 ({len(task.results.get('creds_found', []))})\n"
        for cred in task.results.get('creds_found', []):
            report += f"  - {cred.get('service')}://{cred.get('user')}:{cred.get('pass')}\n"
        
        report += "\n" + "=" * 50
        
        report_path = os.path.join(self.workspace, f"report_{task.task_id}.txt")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        await self.send_update("success", f"报告已保存: {report_path}")


_orchestrator = None

def get_orchestrator(executor=None, workspace: str = "/tmp/redops") -> ReconOrchestrator:
    global _orchestrator
    if _orchestrator is None and executor:
        _orchestrator = ReconOrchestrator(executor, workspace)
    return _orchestrator

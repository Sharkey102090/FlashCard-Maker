from pathlib import Path
import sys
# Add project root to path so `import src...` works
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.core.models import Flashcard, FlashcardSet
from src.core.data_manager import data_manager

CARD_TEXT = '''IDS - Intrusion Detection System
NIDS - Network-based intrusion detection system. Monitors network traffic and detects attacks like smurf attacks. Cannot monitor encrypted traffic or individual hosts.
NIPS - Network Intrusion Prevention System. Sits inline with traffic and blocks malicious activity in real time.
SIEM - Security Information and Event Management. Provides real-time analysis of security alerts from network hardware and applications.
Radius - Remote Authentication Dial-In User Service. Centralized authentication protocol for remote access.
IPSec - Internet Protocol Security. Encrypts traffic using tunnel or transport mode. Includes AH (auth & integrity) and ESP (confidentiality, integrity, auth). Uses port 500 for IKE.
ADC - Application Delivery Controller. Combines load balancing with SSL/TLS acceleration to optimize traffic handling.
SPAN - Switched Port Analyzer. Mirrors traffic from selected ports/VLANs to a monitoring port.
TAP - Test Access Point. Copies network traffic for analysis without introducing a point of failure.
SDN - Software Defined Networking. Decouples control and data planes for flexible network management.
DMZ - Demilitarized Zone. A buffer network between internal systems and the internet.
Extranet - A segmented public-facing network zone for partners and resellers with authorized access.
Intranet - Internal network zone using web-based technologies for employee access.
Sensor - Device or software that collects network data. Used in NIDS/NIPS for real-time awareness.
Virus - Malicious code that runs without user consent and can replicate.
Worm - Self-replicating malware that spreads across networks.
Trojan Horse - Disguised as a legitimate application but contains malicious code.
Spyware - Software that secretly sends user data to another party.
Rootkit - Hidden software that grants escalated privileges and hides its presence.
Botnet - Network of compromised computers used to forward malicious traffic.
Logic Bomb - Malware triggered by specific conditions or events.
Resident Virus - Loads into memory and remains active after host program ends.
Nonresident Virus - Infects targets and exits without staying in memory.
Boot Sector Virus - Infects the first sector of the hard drive and loads before the OS.
Macro Virus - Embedded in Office documents and runs via macros.
Polymorphic Virus - Changes its code/signature to evade detection.
Armored Virus - Uses obfuscation to resist analysis and debugging.
Stealth Virus - Hides its presence by masking file size or location.
Multipartite Virus - Infects both executable files and boot sectors.
Ransomware - Holds data hostage for payment.
Crypto-malware - Encrypts files and demands payment for the decryption key.
Keylogger - Records keystrokes to steal sensitive information.
RAT - Remote Access Trojan. Grants remote control to attackers.
Bot - Automated program controlled remotely, often used for spam or attacks.
Social Engineering - Manipulating people to gain confidential information.
Spear Phishing - Targeted phishing attack on specific individuals.
Phishing - Fraudulent attempt to obtain sensitive info via email.
Vishing - Phishing via phone or VoIP.
Tailgating - Unauthorized entry by following an authorized person.
Shoulder Surfing - Gaining info by observing someone’s screen or keyboard.
Hoax - False threat that causes real harm through user reaction.
Watering Hole Attack - Compromises a site frequently visited by the target.
DoS - Denial of Service. Overloads a system to disrupt service.
DDoS - Distributed DoS. Uses multiple systems to perform a DoS attack.
MITM - Man-in-the-Middle. Intercepts and alters communication between parties.
Buffer Overflow - Overwrites memory by exceeding buffer limits.
XSS - Cross-Site Scripting. Injects malicious scripts into web pages.
XSRF - Cross-Site Request Forgery. Tricks users into executing unwanted actions.
SQL Injection - Injects malicious SQL commands into a database.
Domain Hijacking - Unauthorized takeover of a domain name.
ARP Poisoning - Sends fake ARP replies to redirect traffic.
Zero-day - Exploits unknown vulnerabilities.
Pass the Hash - Reuses hashed passwords for authentication.
Clickjacking - Redirects user clicks to unintended actions.
Session Hijacking - Steals session cookies to impersonate users.
URL Hijacking - Typo-based domain spoofing.
Shimming - Intercepts and redirects calls between components.
Refactoring - Rewriting code for efficiency and clarity.
MAC Spoofing - Fakes MAC address to bypass access controls.
IP Spoofing - Fakes IP address to mislead systems.
Evil Twin - Fake wireless AP mimicking a legitimate one.
Rogue Access Point - Unauthorized AP used to intercept traffic.
Jamming Attack - Disrupts wireless signals to deny access.
WPS - Wi-Fi Protected Setup. Vulnerable to brute-force PIN attacks.
Bluejacking - Sends unsolicited messages via Bluetooth.
Bluesnarfing - Unauthorized access to Bluetooth device data.
RFID - One-way communication using electromagnetic fields.
NFC - Short-range communication using electromagnetic fields.
Birthday Attack - Finds hash collisions to brute-force passwords.
Rainbow Attack - Uses precomputed hash tables to crack passwords.
Dictionary Attack - Uses word lists to guess passwords.
Brute-Force Attack - Tries every possible password or key.
Threat Actor - Entity that discovers or exploits vulnerabilities.
Script Kiddie - Low-skilled attacker using pre-made tools.
Hacktivist - Attacker motivated by political or social causes.
APT - Advanced Persistent Threat. Long-term, stealthy network infiltration.
OSINT - Open-source intelligence from public sources.
Active Reconnaissance - Engages with target (e.g., port scanning).
Passive Reconnaissance - Observes without interacting (e.g., traffic analysis).
Initial Exploitation - Gains access by exploiting vulnerabilities.
Persistence - Maintains access via backdoors or tools.
Black Box - No prior knowledge of the system.
White Box - Full knowledge of system internals.
Gray Box - Partial knowledge of the system.
WHOIS - Public domain lookup tool.
OVAL - XML-based language for describing vulnerabilities.
Intrusive Scan - Actively exploits vulnerabilities to verify them.
Vulnerability Scan - Automated scan for known weaknesses.
Race Condition - Competing code sequences cause unpredictable behavior.
End of Life - Unsupported systems with no vendor updates.
Memory Leak - Unused memory not released, degrading performance.
Integer Overflow - Exceeds max value of an integer, causing errors.
DLL Injection - Inserts malicious code via dynamic link libraries.
ACL - Access Control List. Defines permissions for objects.
AH - Authentication Header. Provides integrity and authentication.
Behavior-based IDS - Detects anomalies based on behavior patterns.
CHAP - Challenge Handshake Authentication Protocol. Uses hashed password for authentication.
DLP - Data Loss Prevention. Monitors and protects sensitive data.
ESP - Encapsulating Security Payload. Provides encryption and integrity.
HSM - Hardware Security Module. Protects cryptographic keys.
Router - Transfers data between networks intelligently.
Signature-based Monitoring - Detects threats using known patterns.
TLS - Transport Layer Security. Encrypts point-to-point communications.
VLAN - Logical separation of network nodes.
VPN - Secure remote access to corporate resources.
ARP - Resolves IP addresses to MAC addresses.
Banner Grabbing - Identifies OS and services via network responses.
Exploitation Framework - Toolset for testing known vulnerabilities.
Honeypot - Decoy system to attract and study attackers.
ICMP - Used for error messages and diagnostics (e.g., ping).
Protocol Analyzer - Captures and decodes network packets.
Steganography - Hides data within other files.
Application Logging - Tracks web app activity for security.
Auditing - Tracks user access for security purposes.
Baseline - Normal activity used to detect anomalies.
Data Exfiltration - Unauthorized data transfer.
Security Baseline - Minimum security configuration for systems.
System Logging - Collects system data for monitoring.
Antispam - Filters unwanted email.
Antivirus - Detects and removes malicious software.
DEP - Data Execution Prevention. Blocks code execution in protected memory.
File Integrity Checker - Verifies file changes using hash comparisons.
Group Policy - Centralized management of user and computer settings.
HIDS - Host-based IDS. Monitors individual systems.
HIPS - Host-based IPS. Blocks threats at host level.
Pop-up Blocker - Prevents unwanted browser pop-ups.
Web Application Firewall - Blocks web-based attacks like XSS and SQLi.
BYOD - Bring Your Own Device. Employees use personal devices for work.
CYOD - Choose Your Own Device. Employees select from approved devices.
COPE - Corporate Owned, Personally Enabled. Company-owned devices with personal use.
Geofencing - Defines geographic boundaries using GPS/RFID.
Jailbreaking - Removes iOS restrictions to install unauthorized apps.
POTS - Traditional analog phone service.
Remote Wipe - Deletes data from lost/stolen devices remotely.
Rooting - Gains root access on Android devices.
Side Loading - Installs apps outside official app stores.
SMS - Short Message Service. Text messaging limited to 160 characters.
Tethering - Shares device’s internet connection with others.
DNS - Resolves domain names to IP addresses.
FTP - Transfers files over TCP networks.
HTTP - Transfers web data between server and browser.
HTTPS - Secure version of HTTP using SSL/TLS on port 443.
LDAP - Accesses directory services over TCP/IP.
NTP - Synchronizes device clocks over networks.
HTTPS - Secure HTTP alternative for encrypted web transactions.
'''


def create_set():
    lines = [l.strip() for l in CARD_TEXT.split('\n') if l.strip()]
    cards = []
    for line in lines:
        if ' - ' in line:
            front, back = line.split(' - ', 1)
        elif ':' in line:
            front, back = line.split(':', 1)
        else:
            front, back = line, ''
        cards.append(Flashcard(front_text=front.strip(), back_text=back.strip()))

    fs = FlashcardSet()
    fs.name = 'CompTIA Security+ Glossary'
    for c in cards:
        fs.add_flashcard(c)

    path = data_manager.save_flashcard_set(fs, filename='comptia_security_plus')
    print('Saved:', path)

if __name__ == '__main__':
    create_set()

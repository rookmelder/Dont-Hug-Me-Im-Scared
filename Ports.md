# Ports

Back to [[Home]].

Found an open port? Find its row and read the linked notes. When a note has `ports:` in its frontmatter, add it here too.

| Port | Service | Notes |
| ---- | ------- | ----- |
| 88 | Kerberos (→ domain controller) | [[AD - Enumeration]], [[AD - AS-REP roasting]], [[AD - Kerberoasting]] |
| 139, 445 | SMB | [[AD - Enumeration]], [[AD - DCSync]], [[AD - Pass-the-hash]], [[Exploitation - EternalBlue MS17-010]], [[AD - LLMNR and NBT-NS poisoning]] (SMB signing / relay) |
| 389, 636, 3268 | LDAP / Global Catalog | [[AD - Enumeration]] |
| 5985 | WinRM | [[AD - Pass-the-hash]] (evil-winrm) |
| 179 | BGP | [[Network - BGP security]] |
| 53 | DNS | [[Network - Rogue DHCP DNS and IPv6 mitm6]] (DNS spoofing) |
| 137 (UDP) | NetBIOS Name Service (NBT-NS) | [[AD - LLMNR and NBT-NS poisoning]] |
| 5355 (UDP) | LLMNR | [[AD - LLMNR and NBT-NS poisoning]] |
| 546, 547 (UDP) | DHCPv6 | [[Network - Rogue DHCP DNS and IPv6 mitm6]] (mitm6) |

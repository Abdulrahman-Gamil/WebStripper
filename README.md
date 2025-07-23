# WebStripper - Multi-Browser Data Extraction Tool for Forensic Investigation & Ethical Hacking

**WebStripper** is a Python-based command-line utility that automates the extraction and decryption of browser artifacts such as:

- Saved credentials  
- Autofill data  
- Browsing history  
- Bookmarks  

This tool is intended for **forensic analysts** and **ethical hackers** working in **Windows environments**. It supports analysis from exported browser profile folders and disk image mounts.


**Supported browsers** include Chrome, Firefox, Edge, Brave, and Opera. WebStripper is optimized for **offline** investigations and supports automated parsing of all detected profiles.
 --- 
 
## Help Menu

<img width="998" height="748" alt="image" src="https://github.com/user-attachments/assets/ed8b9a75-22e9-4493-813a-4d1fc5608568" />


---

## Supported Browsers and Tested Versions

| Browser   | Version Tested     |
|-----------|--------------------|
| Chrome    | 125.0.6422.61      |
| Firefox   | 125.0.2            |
| Edge      | 125.0.2535.67      |
| Brave     | 1.66.110           |
| Opera     | 109.0.5097.38      |

> **Note:** Browser data formats and encryption techniques may evolve over time. Compatibility updates may be required for future versions.



## System Requirements

- Windows operating system  
- Python 3.13.2 (tested version)



## Features and Behavior

- Automatically scans all available profiles in the specified browser data folder.
- For Chromium-based browsers using **DPAPI encryption**, the tool generates a `.dat` file containing the encrypted key (just if you used the -in flag).
- **Decryption of DPAPI-encrypted data** requires access to the original system's **DPAPI master key** located in the exported folder.
- If no input directory is provided, WebStripper defaults to scanning and extracting data from browsers installed on the **local machine**.
- Most extraction functions run automatically with no user intervention required.


---

## Demo

  ![Demo](https://github.com/user-attachments/assets/b5702661-9d24-4ebd-986b-3436313721a3)



> ⚠️ **Note**: Strict Legal Warning This WebStripper tool is for authorized use only. Unauthorized use, or data extraction from any system you do not own or have explicit written permission to test is illegal and unethical. Misuse of this tool may lead to criminal charges, including but not limited to violations of data protection and privacy laws. You are solely responsible for how you use this tool.

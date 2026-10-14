
## Windows command execution: prevent popup consoles

The user explicitly requires that background agent commands must not open or flash additional terminal windows.
- On Windows, every exec_command call must use tty=true. This uses the headless ConPTY path; the non-PTY path has been observed opening Windows Terminal windows on this machine.
- Use login=false for automation unless a profile is explicitly needed. Preserve the requested working directory with workdir.
- For background helpers, use a launcher with UseShellExecute=false and CreateNoWindow=true, or Start-Process -WindowStyle Hidden. Do not use bare start, cmd /c start, or launch interactive terminals for background commands.
- Do not close user-opened terminals or kill active jobs to suppress windows.
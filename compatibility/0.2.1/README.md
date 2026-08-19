# SDK compatibility baseline 0.2.1

`python-sdk-v1.methods.json` is the explicit released 0.2.1 public network
surface used by CI and release checks for 0.3.0. It is copied byte-for-byte
from the generated method contract at the 0.2.1 release boundary.

Release automation must name this file with `--baseline`; the compatibility
tool refuses to infer a baseline from an arbitrary local artifact.

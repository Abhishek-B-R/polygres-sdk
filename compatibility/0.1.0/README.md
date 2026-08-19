# SDK compatibility baseline 0.1.0

`python-sdk-v1.methods.json` is the explicit released 0.1.0 public network
surface used by CI and release checks for 0.2.0. It records the original
retrieval methods and marks Context operations as unavailable in that release.
The baseline uses the first formal stable operation identities because
generated FastAPI function names were not a published SDK contract in 0.1.0.

Release automation must name this file with `--baseline`; the compatibility
tool refuses to infer a baseline from an arbitrary local artifact.

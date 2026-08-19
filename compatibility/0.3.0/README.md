# SDK compatibility baseline 0.3.0

`python-sdk-v1.methods.json` is the explicit released SDK 0.3.0 public network
surface. It is copied byte-for-byte from the generated method contract at the
0.3.0 release boundary.

SDK 0.4.0 compatibility and release checks must name this file with
`--baseline`. The compatibility tool must classify the pgContext-aligned method
names as additive and must report no removals or breaking changes to this
baseline.

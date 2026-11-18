Piano SVSep (https://github.com/CPJKU/piano_svsep), commit
1462e7c28d7adaae033150883a7cb00238ee364a, is included under the MIT license
in LICENSE. The model checkpoint is downloaded separately from that commit and
verified by SHA-256 before loading. The vendored code corrects a comparison of
adjacent tie endpoints in utils/vocsep.py. Omnizart uses only staff predictions
on note events and does not use the upstream score exporter.

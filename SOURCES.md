# Source and publication record

This repository publishes the existing local numerical qualification, including
its registered development inputs, source, generated C, result JSON/CSV and
figures. The tracked history through `92572bb1cf61bd5691c9d088431e2ef3862b7a37`
was reviewed before publication. Ignored virtual environments, build products
and final cases are absent from every published tree. The final-case hash in
`registration.json` is a commitment; the cases and their answers are not public.

The owner's instruction delegates using the existing staging name
`control-code-verification`. It authorizes source publication and CI reproduction,
without supplying functional branch requirements, reviewer sign-off, integration
qualification or a paper-release decision. The original failsafe study remains
paused in [px4-failsafe-differential-testing](https://github.com/500ft/px4-failsafe-differential-testing).

## Code and dependency records

| Material | Source / redistribution record |
| --- | --- |
| Intent, reference, verifier, plotting code and synthetic development traces | Existing owner-authored staging history; published under the owner's instruction. No blanket project license is added by this task. |
| Generated C and headers | CasADi notices retained in every generated file: runtime content, MIT-0 template code and user-owned code are distinguished. [Code-generation documentation](https://web.casadi.org/docs/#generating-c-code). |
| CasADi and NumPy | Installed from the versions in [requirements.txt](requirements.txt), not vendored or redistributed here. [CasADi package record](https://pypi.org/project/casadi/3.8.1/), [NumPy package record](https://pypi.org/project/numpy/2.5.3/). |
| Numerical result and traces | Original [result](evidence/results.json) identifies compiler, package versions, generated source, binary and trace hashes. Original compiler paths are retained as execution provenance; those host directories are not included. |
| Scientific figures | [Manifest](evidence/figure.json) records data, config, generator and style-helper hashes. [figure_style.py](figure_style.py) sets the shared figure rules. The owner's enclosure reference informed the earlier styling. No enclosure data is included. |
| Prior-work references | [references.bib](references.bib) holds the Conrad 2009 and Stürmer, Weinberg and Conrad 2005 entries cited in the README prior-work section, copied from the 2026-10-09 literature review. |

No PX4 source, public flight logs, credentials or third-party datasets are
included in this successor. The generated artifacts compile independently of
the CasADi runtime; Python generation still uses the pinned CasADi package.

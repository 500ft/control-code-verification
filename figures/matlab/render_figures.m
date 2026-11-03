function render_figures(outDir)
%RENDER_FIGURES Redraw the committed figure and typeset-table sources.
%   Run from the repository root:
%     matlab -batch "addpath('figures/matlab'); render_figures"
%   Reads only committed files (evidence/traces.csv, spec.json and the
%   observational summary JSON files). Writes figures/core-qualification.pdf
%   and .png plus the LaTeX table fragments figures/observational-*.tex.
%   Each item runs in its own try/catch so one failure does not stop the rest.

here = fileparts(mfilename('fullpath'));
root = fileparts(fileparts(here));
if nargin < 1, outDir = fullfile(root, 'figures'); end
if ~isfolder(outDir), mkdir(outDir); end
addpath(here);
S = fig_style();

failed = 0;
try
    make_core_qualification(root, outDir, S);
    fprintf('ok core-qualification\n');
catch err
    failed = failed + 1;
    fprintf('FAILED core-qualification: %s\n', getReport(err, 'extended', 'hyperlinks', 'off'));
end
try
    make_observational_tables(root, outDir);
    fprintf('ok observational tables\n');
catch err
    failed = failed + 1;
    fprintf('FAILED observational tables: %s\n', getReport(err, 'extended', 'hyperlinks', 'off'));
end
if failed > 0
    error('render_figures:failed', '%d item(s) failed', failed);
end
end

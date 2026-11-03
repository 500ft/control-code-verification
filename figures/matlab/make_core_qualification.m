function make_core_qualification(root, outDir, S)
%MAKE_CORE_QUALIFICATION Draw figures/core-qualification.{pdf,png}.
%   Inputs: evidence/traces.csv (traces reversal and constant_unsaturated)
%   and spec.json. Top row: exact intent and compiled C on the reversal
%   trace; hollow circles mark the steps flagged in the branch_issue column.
%   Bottom row: absolute error of compiled C and the analytical bound on the
%   constant-input trace. Blue is exact arithmetic (intent, bound); orange is
%   compiled C. The words of the finding live in the caption file.

src = fullfile(root, 'evidence', 'traces.csv');
spec = jsondecode(fileread(fullfile(root, 'spec.json')));
opts = detectImportOptions(src, 'TextType', 'string');
opts = setvartype(opts, {'variant', 'trace', 'reset', 'branch_issue'}, 'string');
T = readtable(src, opts);
variants = string(fieldnames(spec.variants))';
limit = spec.domain.state_abs_max;
assert(isequal(variants, ["zero_reset", "tracking_reset"]), 'unexpected variants in spec.json');

fig = figure('Visible', 'off', 'Units', 'centimeters', 'Position', [2 2 18.3 11.6]);
tl = tiledlayout(fig, 2, 2, 'TileSpacing', 'compact', 'Padding', 'compact');
letters = 'abcd';
ax = gobjects(2, 2);

for col = 1:2
    v = variants(col);
    R = T(T.variant == v & T.trace == "reversal", :);
    C = T(T.variant == v & T.trace == "constant_unsaturated", :);
    issue = R.branch_issue == "True";
    % Checks behind the caption: compiled C equals exact intent on every
    % reversal step, the flagged steps sit on the clamp, and the constant
    % trace stays at least 100 times below its bound with no flagged step.
    assert(height(R) == 256 && height(C) == 64, 'unexpected trace lengths');
    assert(all(R.abs_error_rad_s == 0), 'reversal trace is not exact');
    assert(nnz(issue) == 2 && all(abs(R.c_rad_s(issue)) == limit), 'clamp steps');
    assert(~any(C.branch_issue == "True"), 'constant trace has a flagged step');
    assert(min(C.bound_rad_s ./ C.abs_error_rad_s) >= 100, 'bound margin');

    % (a), (b): reversal trace
    a = nexttile(tl, col); hold(a, 'on'); ax(1, col) = a;
    yline(a, [-limit limit], ':', 'Color', S.c.grey, 'LineWidth', 0.8);
    plot(a, R.time_s, R.intent_rad_s, '-', 'Color', S.c.blue, 'LineWidth', 2.6);
    plot(a, R.time_s, R.c_rad_s, '-', 'Color', S.c.orange, 'LineWidth', 0.8);
    k = 1:16:height(R);
    plot(a, R.time_s(k), R.c_rad_s(k), 'o', 'MarkerSize', 3.2, ...
        'MarkerFaceColor', S.c.orange, 'MarkerEdgeColor', 'none');
    plot(a, R.time_s(issue), R.c_rad_s(issue), 'o', 'MarkerSize', 7.5, ...
        'MarkerFaceColor', 'none', 'MarkerEdgeColor', S.c.orange, 'LineWidth', 1.1);
    set(a, 'XLim', [0 8.15], 'XTick', 0:2:8, 'YLim', [-2.45 2.45], 'YTick', -2:2);
    text(a, 7.95, -0.95, sprintf('%s, $\\tau = %g$ s', strrep(v, '_', '-'), spec.variants.(v).tau), ...
        'FontSize', S.size.note, 'Color', S.c.ink, 'HorizontalAlignment', 'right');
    if col == 1
        text(a, 0.55, 1.5, 'exact intent', 'Color', S.c.blue, 'FontSize', S.size.label);
        text(a, 0.85, 0.95, 'compiled C (binary32)', 'Color', S.c.orange, 'FontSize', S.size.label);
        t5 = R.time_s(find(issue, 1, 'last'));
        text(a, t5 + 0.3, 1.62, {'clamp step,', 'branch open'}, 'FontSize', S.size.note, ...
            'Color', S.c.ink, 'VerticalAlignment', 'top');
        text(a, 7.95, -limit + 0.13, sprintf('rate clamp $\\pm%g$ rad/s', limit), ...
            'FontSize', S.size.note, 'Color', S.c.grey, 'HorizontalAlignment', 'right', ...
            'VerticalAlignment', 'bottom');
    end

    % (c), (d): constant-input trace, log scale
    b = nexttile(tl, 2 + col); hold(b, 'on'); ax(2, col) = b;
    plot(b, C.time_s, C.bound_rad_s, '-', 'Color', S.c.blue, 'LineWidth', 1.4);
    plot(b, C.time_s, C.abs_error_rad_s, '-', 'Color', S.c.orange, 'LineWidth', 0.8);
    k = 1:8:height(C);
    plot(b, C.time_s(k), C.abs_error_rad_s(k), 'o', 'MarkerSize', 3.2, ...
        'MarkerFaceColor', S.c.orange, 'MarkerEdgeColor', 'none');
    set(b, 'YScale', 'log', 'XLim', [0 2.04], 'XTick', 0:0.5:2, ...
        'YLim', [5e-11 3e-4], 'YTick', 10.^(-10:-4), 'YMinorTick', 'off');
    if col == 1
        x = 1.05; yb = interp1(C.time_s, C.bound_rad_s, x);
        text(b, x, yb / 2.2, 'worst-case bound', 'Color', S.c.blue, ...
            'FontSize', S.size.label, 'VerticalAlignment', 'top');
        text(b, x, 5.5e-8, '$|x_{\mathrm{C}} - x_{\mathrm{exact}}|$', 'Color', S.c.orange, ...
            'FontSize', S.size.label, 'VerticalAlignment', 'bottom');
    end
end

for r = 1:2
    for col = 1:2
        a = ax(r, col);
        title(a, ['\textbf{' letters(2 * (r - 1) + col) '}'], 'Interpreter', 'latex', ...
            'FontSize', S.size.letter);
        a.TitleHorizontalAlignment = 'left';
        xlabel(a, 'Elapsed time $t$ (s)');
        if r == 1
            a.YTickLabel = {'$-2$', '$-1$', '$0$', '$1$', '$2$'};
        else
            a.YTickLabel = arrayfun(@(e) sprintf('$10^{%d}$', e), -10:-4, 'UniformOutput', false);
        end
        if col == 2
            a.YTickLabel = {};
        end
    end
end
ylabel(ax(1, 1), 'Commanded rate (rad/s)');
ylabel(ax(2, 1), 'Absolute error (rad/s)');
export_pair(fig, fullfile(outDir, 'core-qualification'));
end

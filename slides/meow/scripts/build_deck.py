#!/usr/bin/env python3
"""Build the web presentation from frozen evidence. Edit the narrative here."""

from html import escape
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from inline_math import format_html

DECK = Path(__file__).resolve().parents[1]
DATA = DECK / "data"
summary = json.loads((DATA / "summary.json").read_text())
reference = json.loads((DATA / "reference/metrics.json").read_text())
local = {case: json.loads((DATA / f"local/published-boundaries-20260908/{case}.json").read_text())
         for case in ("qa", "qh")}
slides = []


def p(text):
    return f"<p>{text}</p>"


def eq(tex):
    return f'<div class="equation"><span class="math-display" data-tex="{escape(tex, quote=True)}"></span></div>'


def inline(tex):
    return f'<span class="math-inline" data-tex="{escape(tex, quote=True)}"></span>'


def panel(title, body, kind=""):
    return f'<article class="panel {kind}"><div class="panel-title">{title}</div>{body}</article>'


def grid(*items):
    return '<div class="grid-2">' + "".join(items) + "</div>"


def stack(*items):
    return '<div class="stack">' + "".join(items) + "</div>"


def callout(text):
    return f'<div class="callout"><p>{text}</p></div>'


def table(headers, rows):
    return '<div class="table-wrap"><table class="measure"><thead><tr>' + "".join(
        f'<th scope="col">{h}</th>' for h in headers) + '</tr></thead><tbody>' + "".join(
            "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows) + "</tbody></table></div>"


def figure(name, alt, caption="", kind=""):
    return f'<figure class="result-figure {kind}"><img src="assets/{name}" alt="{escape(alt, quote=True)}">' + (
        f"<figcaption>{caption}</figcaption>" if caption else "") + "</figure>"


def code(text):
    return "<pre class=commands><code>" + escape(text) + "</code></pre>"


def process(items):
    return '<div class="process">' + "".join(
        f'<div class="process-node"><span class="node-step">{i:02d}</span><h3>{title}</h3><p>{body}</p></div>'
        for i, (title, body) in enumerate(items, 1)) + "</div>"


def add(title, body, source, notes, chapter="Code & derivatives", eyebrow=None, cls=""):
    number = len(slides) + 1
    slides.append(f'''<section class="slide {cls}" data-title="{escape(title, quote=True)}" data-chapter="{escape(chapter, quote=True)}" data-summary="{escape(eyebrow or title, quote=True)}">
<header class="slide-header"><div><p class="eyebrow">{eyebrow or chapter}</p><h2>{title}</h2></div><span class="slide-index">{number:02d}</span></header>
<div class="content narrative">{body}</div>
<footer class="slide-footer"><span>{source}</span><span class="footer-rule"></span><span>meow × cuMES</span></footer>
<aside class="speaker-notes">{notes} Full source paths, revision distinctions, and measurement qualifications are in evidence.md. All objective values in this deck mean squared residual norm, twice the TRF cost.</aside>
</section>''')


def sci(value, digits=5):
    return f"{value:.{digits}e}"


def run(campaign, case, method=""):
    return summary["runs"][f"{campaign}/{case}" + (f"-{method}" if method else "")]


add("Optimizing quasisymmetry with meow",
    '<div class="hero"><div><p class="dek">From boundary coefficients<br>to a quasisymmetric equilibrium.</p>'
    '<div class="tag-row"><span class="tag">C++20 · TRF</span><span class="tag">cuMES tangents</span><span class="tag free">Landreman QA / QH</span></div></div>'
    '<div class="hero-metrics">' + panel("Dense optimization problem", '<strong class="hero-number">120</strong>' + p("boundary variables at QH mode 5")) +
    panel("Measured full construction speed", '<strong class="hero-number amber paired">2.73× / 2.65×</strong>' + p("QA / QH · four cold FD workers + Broyden"), "free") + '</div></div>',
    "meow de1b324 · archived TITAN Xp campaigns · new accuracy checks: 2026-09-08",
    "meow is the Magnetic Equilibrium Optimizer Workbench. The speed headline belongs to parallel finite differences plus secant reuse, not the experimental equilibrium-tangent path. Historical wall comparisons are single complete runs against the cold controls, not repeated timing medians.", chapter="Orientation")

add("Two questions for this presentation", grid(
    panel("01 · How the optimization works", p("Which work belongs to meow and which belongs to cuMES? How can an equilibrium tangent replace a nonlinear finite-difference solve?") + p("Measure both execution time and the final objective.")),
    panel("02 · What has been reproduced", p("Reconstruct QA and QH from analytic seeds. Check the published boundaries with an independent equilibrium solver.") + p("Keep construction, final refinement, and high-resolution re-solves distinct."), "free")),
    "Implementation + saved runs + Landreman–Paul supplemental data",
    "The evidence covers completed analytic-seed constructions and new published-boundary equilibrium solves. It does not establish completion of the entire final-refinement optimization or particle-orbit validation.", chapter="Orientation")

add("meow closes the loop around cuMES", process([
    ("Boundary x", "meow selects absolute Fourier coefficients and a fixed accepted-axis predictor."),
    ("Equilibrium u(x)", "cuMES validates the fixed-boundary problem and solves its multigrid force balance on the GPU."),
    ("Residual r(x)", "meow samples fields and profiles, then forms QS, aspect, and optional mean-iota residuals."),
    ("Jacobian J", "Use cold differences, retained equilibrium tangents, or a safeguarded secant update."),
    ("TRF proposal", "A dense local least-squares model proposes a boundary step within a trust region."),
    ("Accept + checkpoint", "Evaluate the trial; update the radius, accepted axis, and saved input. Repeat."),
]), "meow de1b324 · apps/cumes_landreman_optimize.cpp · src/trf.cpp",
    "The base C++20/Eigen optimizer has no CUDA dependency and is independent of SciPy. The cuMES integration publishes equilibria and directional derivatives; cuMES does not know the QS objective. A failed off-center equilibrium becomes a finite barrier residual so the optimizer can contract the step. Initial equilibrium failure is an error.")

add("Optimize the boundary, hold its scale", stack(
    eq(r"R=\sum_{m,n} R^c_{mn}\cos(m\theta-nn_{fp}\zeta),\qquad Z=\sum_{m,n} Z^s_{mn}\sin(m\theta-nn_{fp}\zeta)"),
    table(["Maximum active mode k", "1", "2", "3", "4", "5"], [["Boundary variables: 4k(k+1)", "8", "24", "48", "80", "120"]]),
    grid(panel("Parameterization", p("Stellarator symmetry retains RBC and ZBS. At m = 0, keep only positive n; for m ≥ 1, keep " + inline(r"-k\le n\le k") + ".")),
         panel("Scale and resolution", p("RBC(0,0) stays fixed at 1. Optimizer cutoff k and the cuMES equilibrium basis are separate controls.")))),
    "meow de1b324 · StellaratorSymmetricBoundaryParameterization::make_modes",
    "x stores absolute coefficient values rather than coefficient deltas. This preserves the archived SIMSOPT relative finite-difference rule. ZBS(0,0) is a zero sine basis. The boundary-tangent bridge maps signed toroidal harmonics into cuMES's real-parity folded basis; it is not simply a flattened JSON array.")

add("TRF turns residuals into boundary steps", stack(
    eq(r"\min_x \tfrac12\|r(x)\|^2,\qquad q(p)=\tfrac12\|r+Jp\|^2,\qquad \|D^{-1}p\|\le\Delta"),
    grid(panel("Model + proposal", p("Form the dense scaled Hessian from JᵀJ. Solve the trust-region quadratic; the general library also handles bounds with Coleman–Li scaling and reflected steps.")),
         panel("Trial + acceptance", p("Compare actual and predicted reduction. Good trials update the boundary and axis predictor; poor trials shrink the radius. ftol, xtol, and gtol stop the run."))),
    callout("A small step satisfies xtol. It does not certify a good QS objective or an accurate Jacobian.")),
    "meow de1b324 · src/trf.cpp · TrfOptions / TrfResult",
    "The equation shows the unconstrained local model used to explain the Landreman workflow. The bound-constrained implementation adds the Coleman–Li model diagonal and considers reflected and Cauchy steps. The dense library is intended for modest variable counts and expensive residuals. Printed TRF cost equals one half of the objective used in benchmark summaries.")

add("A Jacobian is the expensive part", grid(
    panel("Black-box finite differences", eq(r"J_j\approx\frac{r(x+h_je_j)-r(x)}{h_j}") +
          p("Each column requires a perturbed, converged equilibrium and target evaluation. At mode 5: 120 perturbations per full refresh, plus the cached center.")),
    panel("Extra information from cuMES", eq(r"F_u\,u_j=-F_{x_j},\qquad J_j=T_{x_j}+T_u u_j") +
          p("Retain the final-grid linearization. Solve a linear equilibrium response per boundary direction, then apply meow’s analytic target chain rule."), "free")),
    "meow LandremanResidual::jacobian · cuMES EquilibriumLinearization",
    "F is discrete force balance, u contains R, Z, and lambda, and T returns the complete target residual vector. This is forward implicit differentiation, not an adjoint and not differentiation through the whole multigrid history. Dense Jacobian cost still scales with the number of boundary directions.")

add("The tangent crosses a clear API boundary", stack(
    process([("Retain", "EquilibriumLinearization owns the converged force linearization and iterative solve session."),
             ("Differentiate", "solve_boundary_tangent maps a BoundaryTangent to the spectral state response."),
             ("Materialize", "materialize_tangent publishes field/profile derivatives; meow applies QS and size JVPs.")]),
    table(["Current analytic selector", "Policy at meow de1b324"], [
        ["Linear solve", "relative tolerance 5×10⁻⁶ · absolute 10⁻¹¹ · restart 300 · cap 1,000"],
        ["Cold FD fallback", "All m=0 boundary directions; failed or nonfinite tangent columns"],
        ["Status", "Experimental hybrid Jacobian; cold finite differences remain the default"]])),
    "LandremanResidual::jacobian · boundary_parameterization.hpp · *_target_jvp.hpp",
    "This table describes current code, not the looser 1e-4 tangent setting in the early September 2 benchmark. At cutoff k there are " + inline(r"2k") + " designated m=0 black-box columns. The RHS and Jacobian products are analytic CUDA JVPs; cuMES solves the retained system with restarted GMRES and preconditioning. The meow target is outside cuMES.")

qh_tangent = run("early-tangent", "qh", "analytic")
qh_fd = run("early-tangent", "qh", "finite-difference")
add("Tangents remove nonlinear work", table(["Full QH construction · early experiment", "Cold FD", "Tangent"], [
    ["Accepted optimizer iterations", "88", "218"],
    ["Equilibrium evaluations", "4,303", "253"],
    ["Nonlinear equilibrium iterations", "12,203,424", "474,719"],
    ["Tangent Jacobians", "0", "223"],
    ["Tangent linear iterations", "0", "635,648"],
]) + callout(f"{4303/253:.1f}× fewer equilibrium evaluations and {12203424/474719:.1f}× fewer nonlinear iterations. More optimizer steps and linear work remain."),
    "Archived 2026-09-02 · meow 8eac01e · cuMES 4bf4d88 · QH run.log",
    "These are complete-workload counters summed from stage summaries, not CUDA kernel counts. The raw QH logs are preserved in data/archived/early-tangent. This run's final objective is 23.9 times the FD control, so work elimination alone is not equivalent-result acceleration.")

rows = []
for case in ("qa", "qh"):
    fd, tangent = run("early-tangent", case, "finite-difference"), run("early-tangent", case, "analytic")
    rows.append([case.upper(), f"{fd['wall_seconds']:,.2f} → {tangent['wall_seconds']:,.2f} s",
                 f"{fd['wall_seconds']/tangent['wall_seconds']:.3f}×", sci(fd["objective"]), sci(tangent["objective"]),
                 f"{tangent['objective']/fd['objective']:,.1f}×"])
add("Early speed comes with worse endpoints", table(["Case", "FD → tangent wall", "Raw speed", "FD objective", "Tangent objective", "Objective ratio"], rows) +
    callout("3.248× QA and 2.351× QH are raw wall-time ratios. Neither run qualifies as acceleration to the same optimization quality."),
    "Archived TITAN Xp · double Release · 2026-09-02 · one complete run per variant",
    "Runs shared the analytic boundaries, deterministic QA seed, target, continuation, equilibrium gate, and accepted-axis policy. Iteration-equilibrium serialization was disabled. All stages ended by xtol, not an evaluation safeguard. Initial meow/cuMES revisions: 8eac01e/4bf4d88. The two QA raw logs are absent from the retained campaign; timings and boundaries survive, while endpoints are independently documented in the frozen meow investigation.")

add("Check the whole Jacobian, then the endpoint", grid(
    panel("A direction can look accurate", p("After the cuMES correction, QH objective directional derivatives differ by at most <strong>0.705%</strong> in the hybrid check.") +
          p("But complete target-residual columns still differ by <strong>2.95–11.68%</strong>. The 1% column gate is not met.")),
    panel("TRF uses more than Jᵀr", eq(r"g=J^Tr,\qquad H\approx J^TJ") +
          p("A good directional objective derivative can hide a different curvature model. Tightening GMRES to 10⁻⁸ still leaves a 7.77% worst column difference."), "free")),
    "meow fc7e66b / 70bdc94 · corrected tangent qualification",
    "The column oracle solves perturbed nonlinear equilibria; the target chain itself had about 0.116% worst discrepancy in the isolation experiment. Avoid calling a general lambda harmonic a pure gauge: it affects the coupled equilibrium response. The two zero-basis lambda directions do vanish through the public target bridge. No finite-difference column is accepted merely because a linear force residual is small.")

add("Correct wiring changes the tangent result", grid(
    panel("cuMES defect and correction", p("The dual inverse transform wrote constraint fields into buffers that the constraint operator did not read. Commit <strong>8c61395</strong> connects the views.") +
          p("Commit <strong>f1a3ed7</strong> initializes tangent de-aliasing scratch found by Compute Sanitizer.")),
    panel("Measured corrected response", table(["Centered Solovev restart oracle", "Difference"], [
        ["Aggregate spectral state", "0.228%"], ["Published equilibrium fields", "0.514%"]]) +
          p("The harder QH columns still fail the agreed 1% target-column gate."), "free")),
    "cuMES 8c61395 / f1a3ed7 · meow reproduction investigation",
    "These are archived diagnostic results. The defect was in the tangent-owned constraint wiring; the nonlinear path already used the right views. Historical 96/96 cuMES and 10/10 meow test results in the investigation were not rerun for this presentation. Tighter residuals and passing unit tests still require an end-to-end optimization-quality check.")

rows = []
for case in ("qa", "qh"):
    fd, corrected = run("early-tangent", case, "finite-difference"), run("corrected-tangent", case, "analytic")
    rows.append([case.upper(), f"{fd['wall_seconds']:,.2f}", f"{corrected['wall_seconds']:,.2f}",
                 f"{fd['wall_seconds']/corrected['wall_seconds']:.3f}×", sci(corrected["objective"]),
                 f"{corrected['objective']/fd['objective']:.2f}×"])
add("Corrected tangent: no qualified speedup yet", table(["Case", "Cold FD (s)", "Corrected (s)", "Speed / FD", "Final objective", "Objective / FD"], rows) +
    callout("Corrected endpoints improve greatly, but QA takes 1.71× the control time and QH takes 1.08×. Both objectives remain worse."),
    "Archived 2026-09-03 · cuMES f1a3ed7 · meow fc7e66b · same TITAN Xp controls",
    "The corrected runs stop normally by ftol or xtol. QA uses 92 accepted iterations, 584 equilibrium evaluations, and 849279 linear iterations. QH uses 153, 1000, and 1173790 respectively. Cold timings are the historical controls, not new paired reruns on the corrected dependency. This campaign does not support claiming a current production tangent speedup.")

add("Reuse reliable derivatives between refreshes", stack(
    eq(r"s=x_{k+1}-x_k,\quad y=r_{k+1}-r_k,\qquad J_{k+1}=J_k+\frac{(y-J_ks)s^T}{s^Ts}"),
    grid(panel("Safeguarded Broyden update", p("An accepted step supplies a secant. Refresh from cold finite differences when the model becomes unreliable or the refresh interval is reached.")),
         panel("Qualified aggressive settings", table(["Refresh interval", "8 accepted steps"], [
             ["Minimum reduction ratio", "0.05"], ["Maximum relative secant error", "0.5"]]), "free")),
    callout("Broyden uses already observed residual changes. It is separate from cuMES equilibrium-tangent information.")),
    "meow src/trf.cpp · archived aggressive-Broyden campaigns · current JSON parameters",
    "The implementation refreshes when <code>steps_since_refresh+1</code> reaches 8, the actual/predicted ratio is below 0.05, the relative secant discrepancy exceeds 0.5, or a secant is invalid. Extending the interval to 16 made the QA mode-1 gate slower (21.95 vs 12.86 s) and was rejected. Perturbed samples still follow the cold multigrid path; only compatible stage centers can reuse an accepted snapshot.")

add("Schedule independent columns concurrently", table(["Mode-1 Jacobian · 8 columns", "Serial", "2 workers", "4 workers", "4-worker matrix difference"], [
    ["QA", "2.829 s", "1.263 s", "0.867 s", "0 · bit-exact"],
    ["QH", "2.282 s", "1.035 s", "0.735 s", "0 · bit-exact"],
]) + grid(panel("Independent cuMES instances", p("Each worker owns its solve and target evaluation. The center residual and accepted-axis predictor stay fixed across the batch.")),
          panel("Measured saturation", p("Eight workers: a QA perturbation lost convergence. QH stayed exact but slowed from 0.718 to 0.789 s in that separate diagnostic."), "free")),
    "Archived worker-count checks · TITAN Xp · meow reproduction record §§worker scaling",
    "Single-Jacobian wall timings include perturbed solves and target work. The 8-worker comparison is a different session, so its 0.718 s four-worker control should not replace the 0.735 s value in the first table. The documented four-worker check keeps peak process RSS below 198 MB. No timing is multiplied into an end-to-end claim.")

add("Qualified full constructions are faster", table(["Jacobian strategy", "QA wall (s)", "QH wall (s)", "End result"], [
    ["Historical cold FD", "1,537.26", "3,262.78", "Control objectives"],
    ["Serial aggressive Broyden", "1,209.77", "2,681.44", "Same endpoints as both parallel Broyden runs"],
    ["2 workers + Broyden", "800.78", "1,741.81", "Same equilibrium / nonlinear work as 4 workers"],
    ["4 workers + Broyden", "563.79", "1,232.17", "QA 4.09895e−7 · QH 3.99556e−5"],
]) + callout("Four workers give 1.420× QA / 1.414× QH over two workers, with matching trajectories. Versus historical cold FD: 2.727× / 2.648×, with improved objectives."),
    "Archived 2026-09-04 · full QA 1→4 / QH 1→5 · TITAN Xp · double Release",
    "Four-worker raw logs and GNU time records are preserved. QA: 77 accepted iterations, 2130 equilibrium solves, 4450488 nonlinear iterations, 35 secant updates, RSS 325656 KiB. QH: 113, 3520, 9876526, 52, RSS 356088 KiB. This is one complete timing per configuration, no repeat-based uncertainty estimate. The full speed versus cold includes changes of optimization trajectory; only the worker-count comparisons preserve the aggressive-Broyden trajectory. Historical dependency identity for the four-worker executable is not recorded in the retained time file; the implementation lineage is documented separately.")

add("Time and quality must improve together", figure("speed-and-quality.svg",
    "Two plots compare wall time and final objective relative to cold finite differences. Early tangents are fast but inaccurate. Corrected tangents are slower and still worse. Four-worker Broyden improves both measures.",
    "Lower-left is better. Point ratios come from the archived complete runs; no interpolation or timing-error bars are implied."),
    "data/summary.json · derived ratios · early / corrected tangent and four-worker campaigns",
    "This closes part one: cuMES's extra tangent information removes many nonlinear solves, but the saved full optimization evidence does not qualify it as a speedup. The demonstrated fast path combines reliable cold Jacobian samples, Broyden reuse, and GPU concurrency.")

add("Reproducing Landreman QA and QH",
    '<div class="chapter-card"><div class="section-number">02</div><p class="dek">Use the original targets and seeds.<br>Inspect the shapes, convergence history, and independently solved fields.</p></div>',
    'Landreman &amp; Paul · PRL 128, 035001 (2022) · Zenodo v2',
    'The reference cases are the paper’s vacuum QA and QH configurations without the added magnetic-well objective. Primary references: https://doi.org/10.1103/PhysRevLett.128.035001 and https://doi.org/10.5281/zenodo.5645413.', chapter="Landreman reproduction", cls="chapter-slide")

add("The published geometries", figure("published-boundaries.png",
    "Three-dimensional Fourier reconstructions of the published two-field-period QA and four-field-period QH boundaries.",
    "Original published boundary coefficients · common geometric scale · shading represents surface geometry, not |B|.", "geometry") +
    grid(panel("Quasiaxisymmetry · QA", p("nfp = 2 · target aspect ratio 6<br>Symmetric Boozer harmonics have n = 0.")),
         panel("Quasihelical symmetry · QH", p("nfp = 4 · target aspect ratio 8<br>Per-period helicity −1; physical N = −4."), "free")),
    "Zenodo v2 · configurations/new_QA and configurations/new_QH · generated Fourier surfaces",
    "These are renderings of the original reference geometry, not the result of the new cuMES solves. B quasisymmetry concerns field strength in Boozer coordinates and does not require an axisymmetric physical boundary. All plotted surfaces are reconstructed from stored Fourier coefficients with the VMEC " + inline(r"m\theta-n\zeta") + " convention.", chapter="Landreman reproduction")

add("Three distinct reproduction comparisons", table(["Comparison", "Starting data", "What it establishes"], [
    ["Analytic-seed construction", "Runs 021 (QA) / 039 (QH)", "meow can rediscover low-QS shapes through mode continuation"],
    ["Final-refinement target oracle", "Terminal optimization wouts · ns=75", "The independent target evaluator matches saved SIMSOPT objectives"],
    ["Published-boundary re-solve", "configurations/new_QA / new_QH · ns=201", "cuMES solves the published geometry; compare its fields and QS profile"],
]) + callout("qa_analytic.json → construction. qa_start.json → final refinement. qa.json → published-boundary evaluation. QH uses the corresponding three inputs."),
    "meow examples/landreman/README.md · frozen VMEC baselines",
    "The two final-refinement runs activate boundary modes 4 then 5 and change the surface weights. Their terminal VMEC outputs are distinct from the later higher-resolution convergence re-solves. A single objective cannot be moved between these baselines. Saved local opt-qa-test/opt-qh-test evidence completes mode 4 only; this deck does not claim a completed independent mode-5 final refinement.", chapter="Landreman reproduction")

add("Match the physical QS functional", stack(
    eq(r"Q=\frac{(N-\iota M)(\mathbf B\times\nabla\psi)\!\cdot\nabla B+(MG+NI)\,\mathbf B\!\cdot\nabla B}{B^3}"),
    eq(r"r_{s,a}=\sqrt{w_s\frac{|\sqrt g_{s,a}|}{\sum_b|\sqrt g_{s,b}|}}\;Q_{s,a},\qquad f_{QS}=\sum_{s,a} r_{s,a}^2"),
    grid(panel("From equilibrium fields", p("B is field strength. I and G are covariant flux functions; ψ uses the archived flux/sign convention. Normalize the surface quadrature once.")),
         panel("No Boozer solve inside optimization", p("Fourier-resample the cuMES fields and linearly interpolate half-grid quantities to the target surfaces. Boozer analysis comes afterward."), "free"))),
    "meow quasisymmetry_target.hpp · evaluate_landreman_qs.py · archived SIMSOPT metric",
    "The displayed invariant uses the cuMES public orientation convention. The imported VMEC flux derivative is " + inline(r"-\Phi_{\mathrm{edge}}/(2\pi)") + "; the bridge fixes orientation from the Jacobian once, including the cross-product sign. N is physical toroidal helicity, so QH uses −4, not −1. Surface weights multiply squared residuals; residual amplitudes receive their square roots. Linear extrapolation is used at the magnetic axis and edge. This target interpolation is separate from cuMES multigrid B-spline prolongation.", chapter="Landreman reproduction")

add("Keep targets and stages comparable", table(["Setting", "QA construction", "QH construction", "Final refinement"], [
    ["Aspect target", "6", "8", "6 / 8"],
    ["Mean-iota residual", "ῑ − 0.42", "Absent", "Absent in both"],
    ["Surface weights", "All 1", "All 1", "QA: 1→30 · QH: 1→2"],
    ["Target sampling", "11 flux surfaces", "s=0, 0.1, …, 1", "63 × 64 points / surface"],
    ["FD relative / absolute step", "3.16228e−3 / 1e−7", "1e−3 / 1e−7", "1e−5 / 1e−9"],
]) + callout("44,352 QS residuals. Append aspect for both cases and mean iota only for QA construction. Objective = QS + scalar residual squares."),
    "meow examples/landreman/*rundown.json · Landreman runs 021 / 039 / 050 / 059",
    "QA construction has 44354 residuals and QH has 44353. The target angular grid covers one field period independently of the equilibrium angular grid. " + inline(r"h_j=\max(h_{\mathrm{rel}}|x_j|,h_{\mathrm{abs}})") + ". The known difference between construction and refinement step sizes is essential at the sparse QA start.", chapter="Landreman reproduction")

add("Unlock shape modes through continuation", table(["Boundary cutoff k", "Variables", "cuMES mpol / ntor", "QA", "QH"], [
    ["1", "8", "3 / 3", "Start", "Start"], ["2", "24", "5 / 5", "Continue", "Continue"],
    ["3", "48", "6 / 6", "Continue", "Continue"], ["4", "80", "6 / 6", "Construction endpoint", "Continue"],
    ["5", "120", "6 / 6", "Final refinement is separate", "Construction endpoint"],
]) + p("Use the imported ns = 12 → 25 → 50 sequence for construction and a common 10⁻¹² equilibrium gate. Carry the accepted axis when adding modes."),
    "meow construction rundowns · LandremanStage · accepted-axis campaign",
    "mpol counts poloidal basis entries, unlike the maximum active boundary m=k. Higher construction modes need raised work allowances: at least 10000 iterations for mpol=ntor=6, and QA mode 4 allows 30000. These are caps, not measured iteration counts. The QH path selects Catmull-Rom radial transfer; that is equilibrium-solver provenance, not a target change.", chapter="Landreman reproduction")

add("A faithful seed needs faithful derivative policy", grid(
    panel("QA starts on a stationary manifold", eq(r"R=1+0.2\cos\theta,\qquad Z=0.2\sin\theta") +
          p("At exact axisymmetry the 3-D tangent cannot see first-order transform growth. The tangent path inserts a deterministic chiral seed of amplitude 10⁻⁴.")),
    panel("Cold solves need a consistent predictor", p("Reusing the refinement FD step left the QA objective at <strong>0.0442</strong> and mean iota near <strong>0.284</strong>.") +
          p("Construction steps plus accepted-axis tracking reach mode-1 objective <strong>0.00962215</strong>; the archive gives ≈<strong>0.0096408</strong>."), "free")),
    "meow dee632f / ce1f6e0 / f7f8f8d · archived diagnosis and corrected construction",
    "The early accepted-axis QA campaign starts exactly axisymmetric and uses the original one-sided construction differences. Later comparative tangent/FD campaigns seed both methods identically at 1e-4. Do not conflate these two QA controls (4.57544e-7 versus 5.94684e-7 final objective). At each accepted step retain the converged m=0 axis; each trial uses that fixed axis plus only its boundary-centerline change. This axis prediction is distinct from hot-restarting all perturbed equilibrium states.", chapter="Landreman reproduction")

for case, cutoff in (("qa", 4), ("qh", 5)):
    cold = summary["accepted_axis_construction"][case]
    cold_endpoint = cold["stages"][-1]["objective"]
    archive_endpoint = summary["archived_stage_objectives"][case][-1]
    fast = run("four-worker-broyden", case)
    add(f"{case.upper()}: construction reaches the reference scale", figure(f"{case}-convergence.svg",
        f"Logarithmic stage-end objective plot for {case.upper()}, comparing the Landreman archive with meow cold finite differences and four-worker Broyden.") +
        table(["Final construction objective", "Landreman", "meow cold FD", "meow 4-worker Broyden"], [
            [f"k={cutoff} · same target definition", sci(archive_endpoint), sci(cold_endpoint), sci(fast["objective"])],
            ["Ratio to Landreman", "1.000", f"{cold_endpoint/archive_endpoint:.3f}", f"{fast['objective']/archive_endpoint:.3f}"],
        ]), "Saved construction logs · Landreman 021 / 039 · accepted-axis and four-worker campaigns",
        f"The cold accepted-axis {case.upper()} campaign totals {sum(s['iterations'] for s in cold['stages'])} accepted steps. The curves show stage endpoints, not equal wall-time samples. Archived intermediate values are rounded as recorded in the investigation; final reference values retain more precision. Paths differ between the independent optimizer/equilibrium implementations. Construction and refinement objectives have different definitions. For QA, the cold construction plotted here predates the shared chiral seed in the timing controls.", chapter="Landreman reproduction", cls="plot-table-slide")
    add(f"{case.upper()}: the reconstructed boundary", figure(f"{case}-construction-shapes.png",
        f"Three {case.upper()} toroidal surfaces show the analytic seed, the meow accepted-axis construction endpoint, and the retained Landreman construction boundary.",
        "Actual Fourier coefficients · common scale · QA rotated by π/nfp to align toroidal phase · geometry shading only.", "geometry") +
        p("QA begins with an axisymmetric torus." if case == "qa" else "QH begins with " + inline(r"R=1+0.2\cos\theta+0.2\cos4\zeta") + " and " + inline(r"Z=0.2\sin\theta-0.2\sin4\zeta") + "."),
        "data/archived/accepted-axis · Zenodo construction wouts · data/reference/boundaries.json",
        "The middle surface is the saved meow cold accepted-axis endpoint. QA has been rigidly rotated by pi/nfp (90 degrees) to align its spontaneously selected toroidal phase with the reference; QH is unrotated. No input or objective data are changed. The right surface uses the last retained run-021/039 construction wout near the endpoint; it may be a finite-difference perturbation, so objective comparisons use the separate accepted-step ledger. These are rediscovered construction geometries, not a claim of coefficient identity or a completed final-refinement run.", chapter="Landreman reproduction")

add("The target oracle reproduces the archived totals", table(["Terminal VMEC output · new CPU evaluation", "QA", "QH"], [
    ["Composite objective", sci(reference["qa-terminal"]["objective"], 10), sci(reference["qh-terminal"]["objective"], 10)],
    ["Weighted QS", sci(reference["qa-terminal"]["qs_total"], 10), sci(reference["qh-terminal"]["qs_total"], 10)],
    ["Unweighted QS", sci(reference["qa-terminal"]["unweighted_qs_total"], 10), sci(reference["qh-terminal"]["unweighted_qs_total"], 10)],
    ["VMEC final grid", "ns=75 · mpol=8 · ntor=6", "ns=75 · mpol=8 · ntor=6"],
]) + callout("The independently evaluated terminal totals match the frozen SIMSOPT values to their printed precision. This verifies the target calculation on the same fields."),
    "New CPU evaluation · terminal wouts 000063 / 000090 · meow evaluate_landreman_qs.py",
    "These are evaluations of existing VMEC outputs, not newly solved VMEC equilibria and not an optimization timing comparison. The final-refinement targets omit mean iota. The QA weighted-QS value is 1.318328430729835e-6 and QH is 3.447629144415016e-5. Source SHA-256 values and full per-surface profiles are saved. The new Python evaluations agree with the frozen investigation's full-precision objective values.", chapter="Landreman reproduction")

add("Published boundaries converge in cuMES", table(["New GPU solve · 2026-09-08", "QA", "QH"], [
    ["Final resolution", "201 × (mpol=16, ntor=12)", "201 × (mpol=8, ntor=8)"],
    ["Total / final-stage iterations", f"{local['qa']['total_iterations']:,} / {local['qa']['final_stage_iterations']}", f"{local['qh']['total_iterations']:,} / {local['qh']['final_stage_iterations']}"],
    ["FSQR / FSQZ / FSQL", " / ".join(sci(local['qa'][k], 2) for k in ("fsqr", "fsqz", "fsql")), " / ".join(sci(local['qh'][k], 2) for k in ("fsqr", "fsqz", "fsql"))],
    ["Aspect ratio", f"{local['qa']['aspect_ratio']:.9f}", f"{local['qh']['aspect_ratio']:.9f}"],
    ["Mean iota", f"{local['qa']['mean_iota']:.9f}", f"{local['qh']['mean_iota']:.9f}"],
    ["Composite objective", sci(local["qa"]["objective"]), sci(local["qh"]["objective"])],
]), "New TITAN Xp · CUDA 12.1 · verify-double Release · meow de1b324 / cuMES f61c959",
    "Both runs meet the adapted 1e-12 force gate. These new pinned-build values differ from the earlier documented cuMES cross-check, whose objectives were 1.78081249318e-6 and 4.72745833797e-5. They are kept separate rather than silently reused. A cause for the revision-to-revision difference was not isolated for this deck. The QH solve explicitly uses Catmull-Rom transfer; QA uses the default B-spline path. Single diagnostic wall times were recorded but are not speed benchmarks.", chapter="Landreman reproduction")

for case in ("qa", "qh"):
    add(f"{case.upper()}: compare the full radial QS profile", figure(f"{case}-qs-profile.svg",
        f"Unweighted surface QS profiles for {case.upper()} show distinct terminal VMEC, high-resolution published VMEC, and newly solved cuMES results on the same eleven target surfaces.") +
        table(["Composite objective", "VMEC terminal · ns=75", "VMEC published · ns=201", "cuMES pinned · ns=201"], [
            [case.upper(), sci(reference[f"{case}-terminal"]["objective"]), sci(reference[f"{case}-published"]["objective"]), sci(local[case]["objective"])]]),
        "data/reference/metrics.json · data/local/published-boundaries-20260908",
        "Profiles plot unweighted surface squared residuals so the radial shape is visible. The table uses the final-refinement weighted composite objective, including aspect. The published and terminal boundary shape is the same to imported precision, but their solved fields and resolutions differ. No ratio between the three curves is a speedup or proof of better physical accuracy. The especially different high-resolution QA QS value is measured directly from the archived wout, not substituted with its terminal-optimization value. Diagnosing discretization sensitivity is outside this slide-only task.", chapter="Landreman reproduction", cls="plot-table-slide")

add("Boozer coordinates expose the reference symmetry", figure("reference-boozer-contours.png",
    "Original Boozer edge field-strength contours show nearly horizontal bands for QA and diagonal bands for QH over one field period.",
    "Original BOOZ_XFORM fields at s = 0.9975 · |B| normalized by each surface’s B₀₀ · reference data, not new cuMES output."),
    "Zenodo v2 · boozmn files in configurations/new_QA and new_QH",
    "The plot directly reconstructs every retained cosine coefficient from the original BOOZ_XFORM files. " + inline(r"\theta_B") + " is vertical, field-period toroidal angle is horizontal. QA depends approximately on theta_B; QH depends approximately on " + inline(r"\theta_B+4\zeta_B") + ". This visualizes the intended magnetic symmetry without claiming that cuMES's new fields have the same Boozer spectrum. A meow/cuMES postprocessed spectrum must also account for its mixed-grid toroidal Jacobian, as documented in plot_boozer_symmetry_breaking.py.", chapter="Landreman reproduction")

add("A spectral diagnostic is a separate check", figure("reference-boozer-spectrum.svg",
    "Original maximum nonsymmetric Boozer coefficient divided by B00 as a function of normalized toroidal flux, for QA and QH.") +
    callout("Reference maximum |Bmn|/B₀₀: QA 4.758×10⁻⁵ · QH 4.822×10⁻⁴. These are spectral amplitudes, not the squared QS objective."),
    "Original BOOZ_XFORM coefficients · nonsymmetric: QA " + inline(r"n\ne0") + "; QH " + inline(r"n\ne-4m"),
    "Each profile normalizes with its local B00 and spans the 200 archived half-grid surfaces, s=0.0025 to 0.9975. The largest value in each file occurs near the edge. This is a reference-only diagnostic. The present deck reproduces equilibrium convergence and target measurements but does not claim a matched new cuMES Boozer spectrum, SPEC Poincare map, or particle confinement result.", chapter="Landreman reproduction")

add("Run the current JSON workflow", grid(
    panel("Pinned integration build", code("cmake -S ../meow -B ../tmp/meow-slides-build \\\n  -DMEOW_BUILD_CUMES_INTEGRATION=ON \\\n  -DMEOW_FETCH_CUMES=ON \\\n  -DCMAKE_BUILD_TYPE=Release\ncmake --build ../tmp/meow-slides-build -j 6")),
    panel("Inspect the supplied fast rundown", code("../tmp/meow-slides-build/cumes_landreman_optimize \\\n  --dry-run \\\n  slides/meow/data/inputs/qa-four-worker.rundown.json") +
          p("Remove <code>--dry-run</code> to optimize; QH has its own rundown. The JSON explicitly sets <code>workers=4</code>, <code>refresh_interval=8</code>, and the 0.05 / 0.5 safeguards."), "free")),
    "Commands from repository root · current meow CLI · supplied QA/QH rundowns validated",
    "Build requirements come from meow README: CMake 3.24+ for fetching, C++20, Eigen, CUDA 11.8+ and a compatible compiler/GPU. The default cuMES dependency is pinned to f61c959334bb62e14c049c66335580b45f63610d; the new measurement used CUDA 12.1. For historical wall reproductions use the historical source and former CLI recorded in evidence.md, not the current command. Changing only a method name does not set the JSON secant safeguards. See README.md for commands with a scratch output path and a stage limit.", chapter="Reproduction & evidence")

add("What the measurements establish", grid(
    panel("Optimization mechanics and speed", p("cuMES supplies a reusable equilibrium response; meow owns the target and Jacobian chain rule.") +
          p("Tangents reduce nonlinear work, but corrected full runs have no qualified speedup. Four-worker Broyden delivers the measured fast constructions.")),
    panel("Landreman reproduction", p("Analytic-seed constructions reach the archived objective scale and recover similar QA/QH shapes.") +
          p("The target oracle matches the original totals. Published-boundary cuMES solves converge, with documented differences in their radial QS profiles."), "free")),
    "evidence.md · frozen raw logs / inputs / source fingerprints · reproducible figures",
    "The new deck makes all three limits explicit: tangent optimization is experimental, force convergence does not imply identical QS quality, and final-refinement completion and orbit validation are not established by these artifacts. Use O for overview and N for speaker notes. Plot and HTML regeneration use local frozen data and do not rerun the GPU solver.", chapter="Reproduction & evidence")

tail = (DECK.parent / "cumes-run/index.html").read_text().split("  </main>", 1)[1]
head = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#04101a"><meta name="description" content="How meow optimizes cuMES equilibria, measured derivative strategies, and Landreman QA/QH reproduction.">
<title>meow · Quasisymmetric equilibrium optimization</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.18.4/dist/katex-swap.min.css" integrity="sha384-UPDcDT9bUBaTMMvcooRxZ1CFTMVIIFEcw5g0pJ7FVdzjmHL/avwg1ZUOyF/iA4Ps" crossorigin="anonymous"><link rel="stylesheet" href="styles.css"><link rel="stylesheet" href="meow.css"><link rel="stylesheet" href="../../typography.css">
</head><body data-deck="meow"><main class="deck" aria-live="polite">
'''
(DECK / "index.html").write_text(format_html(head + "\n".join(slides) + "\n</main>" + tail))
print(f"Built {len(slides)} slides")

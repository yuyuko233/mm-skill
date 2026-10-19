# mm official reference (archived)

> Source: official documentation extracted from <https://bhosmer.github.io/mm/ref.html> (extracted 2026-10-15, matches github.com/bhosmer/mm master).
> Interactive `javascript:` links in the original page were converted to plain text; see `params-reference.md` (English)
> and `params-reference.zh.md` (Chinese) for the curated manual. Official online version:
> <https://bhosmer.github.io/mm/ref.html> (offline copy: `/mm/ref.html` served by serve.py; rendering needs CDN access, content is embedded).
> Chinese translation: [`upstream-ref.zh.md`](upstream-ref.zh.md)

---

# mm - 3D matmul visualizer

Example pane is interactive and session state is saved in URL (reset)

Open the current visualization in its own window at any time with the 
open↗ caption link.

## Interaction
|   | Laptop | Mobile |
| - | ------ | ------ |
| Zoom | Two finger vertical drag, up/down arrows | Pinch |
| Spin | Click + drag, shift-left/right arrows | Tap + drag |
| Pan | Command-click + drag, left/right arrows | Two-finger drag |
| Magnify/reveal | Long click or ctrl-click + drag | Long tap + drag |

## Saving/Sharing
* URL is a complete, sharable configuration
  * note: Safari address bar truncates very long URLs - full URL is also available in the **diag** submenu
* JSON for the corresponding `parameters` configuration object also available in **diag**

## Undo
* **The tool** (use open↗ link)
  records all changes in browser history, back/forward is usable for full undo/redo         
* **This reference** saves session state in the URL but undo capability is limited
    
## Start state
    
The default visualization 
(no saved URL params) visualizes a single matmul `L @ R` of two 32x32 matrices:
* Left argument `L` is initialized in *row major* order. Evenly spaced values 
range from `-1` (red) at top left to `1` (blue) at bottom right.
* Right argument `R` is initialized in *column major* order with the same range of values.
* The result matrix (labeled `L @ R`) contains the result of the matmul. 
* Guide lines run parallel to matrix rows, with a triangle at the `(0, 0)` corner. 
* The guide arrow in the cube's interior points to the result matrix. 
The ***R***ed vane points to the ***R***ight argument and the blue vane 
points to the left argument.

This is just a starting point. We can 
* visualize compound expressions
* model any valid argument shapes and sizes up to practical limits
* specify values using preset initializers, custom expressions or loaded data
* animate a variety of algorithms
* visualize block partitioning and fusion
* customize more or less everything about the visualization itself.

## Quick intuition refresher

* rotate, zoom, and inspect values (see **Interaction**, above)
* animate 
  pairwise dot product, 
  matrix-vector product, 
  vector-matrix product, 
  summed outer products 
  (faster, 
  slower, 
  stop)
* initialize with random values (back to rows and columns)
* some common shapes: 
  wide to narrow (e.g. q/k/v projection), 
  narrow to wide (e.g. low rank factorization), 
  big batch, 
  little batch 
  (back to cube)
* bigger, smaller 
* split matmul along i,
  along j,
  along k
  (unsplit)
* visualize values with local sensitivity - sizes and colors 
  normalized per-matrix rather than across the entire visualization
  (back to global sensitivity)
* hide guides, hide all deco (back to default deco)

A handful of slightly less basic examples, built in a few steps using the menu options described 
in the rest of this guide (links above work on these examples as well, except the shape resets):
* double matmul a la attention: out = (attn = Q @ K) @ V
* attention with input/output projections:
  out = (attn = (Q = input @ wQ) @ (K = wK @ input_t)) @ (V = input @ wV) @ wO
* left-associative chain a la MLP: 
  out = (x1 = (x0 = batch @ w0) @ w1) @ w2
* MLP with low rank decompositions for weights:
  out = (x1 = (x0 = batch @ (w0 = w0_L @ w0_R)) @ (w1 = w1_L @ w1_R)) @ (w2 = w2_L @ w2_R)

# mm Menu

Configuration is specified interactively via the **mm** menu at upper right. 
All options map directly to properties encoded in the URL.
    
* **top level** options 
  configure global properties, mainly the structure of the matmul expression itself
* **left** and **right** submenus 
  configure the left and right arguments of the top level matmul, including initialization and shape
  * If either argument is a subexpression, the corresponding submenu will have its own left and right submenus
* **animation** submenu 
  controls how the matmul computation is animated
* **blocking** submenu 
  configures how the expression is partitioned into blocks
* **layout** submenu 
  controls the orientation and spacing of the expression in 3D space
* **deco** submenu 
  configures decorations like legends and orientation guides, and options for showing numerical values
* **colors and sizes** submenu 
  configures the color and brightness details of how values are mapped
* **diag** submenu 
  contains stats and data, e.g. the current URL, JSON config object, etc.
      

#  
# Top Level

## expr
  
**expr** can be edited directly to specify the structure of the matmul being visualized.
(Alternatively, the structure can be built interactively via the **left** and **right** 
submenus, which configure the properties of the matmul's constituents in any case.)

An expression is of the form `left @ right` or `result = left @ right`, where
* `left` and `right` can be subexpressions
* `result` names the visualized result matrix (if not provided, the expression itself is used)
* parens are used to group right-associative subexpressions and subexpression assignments

When **expr** is edited, existing settings are preserved on a best-efforts basis - in particular when names are reused.

These examples show the effect of simply editing the **expr** of the current visualization, with no other modifications:
* double matmul a la attention: out = (attn = Q @ K) @ V
* left-associative chain: A @ B @ C @ D
  * with named results: X = (ABC = (AB = A @ B) @ C) @ D
* right-associative chain: X = A @ (B @ (C @ D))
  * with named results: X = A @ (BCD = B @ (CD = C @ D))
* left and right subexpressions: (L = LL @ LR) @ (R = RL @ RR) 
  * children beget grandchildren: (L = (LL = LLL @ LLR) @ (LR = LRL @ LRR)) @ (R = (RL = RLL @ RLR) @ (RR = (RRL @ RRR))) 
  * note: the **layout** submenu contains various options
    that can be used to let some air into visualizations of deeply nested saturated expressions like this one -
    for example adding space between subexpressions and their parents, 
    using scattered
    or dense subexpression layouts.
    (back to default)
  * also, for expressions like this one which contain both very small and very large values, it can be useful to set
    sensitivity to local in the
    **visualization** submenu. This normalizes
    element color and size within each matrix, rather than across the entire expression. 
    (back to global)
      
## name

Names the result matrix of the matmul being computed. Can be edited directly,
and/or is synchronized with **expr**.

## epilog

Specifies a function to run on the result matrix after the top level matmul has been calculated.

(Child matmuls will have their own choice of epilogs, in the **left** and **right** submenus.)        

* none: no epilog, result values are unmodified
* relu: relu is applied to result values
* gelu: [gelu](https://arxiv.org/pdf/1606.08415.pdf) is applied to result values
* sigmoid: [sigmoid](https://paperswithcode.com/method/sigmoid-activation) is applied to result values
* silu: [silu](https://arxiv.org/pdf/1702.03118v3.pdf) is applied to result values
* tanh: tanh is applied to result values 
* layernorm: matrix-wide layernorm is applied to result values
* softmax: values are softmaxed by row
* softmax(x/sqrt(k)): values are scaled by the square root of matmul depth, 
  then softmaxed by row (a la scaled dot product attention)
* softmax(tril(x/sqrt(k))): values are scaled by the square root of depth, 
  then the upper triangle is masked, then softmax is applied by row (causal SDPA)
      

#  
# Left and Right

Left and right submenus configure the left and right arguments of the matmul 
being visualized. 

Menu options vary depending on whether the argument is itself a matmul, as described below:
subexpressions can nest to arbitrary depth, and left and right submenus will nest accordingly.

## name

Names this argument. Can be edited directly, and/or is synchronized with **expr**.

## matmul

This checkbox specifies whether the argument is itself a matmul, or just a matrix. 
Subsequent options in the menu depend on the value of this option.

## *Left/Right matrix options (matmul unchecked)*

## h, w

Matrix height and width. The width of the left argument and height of the right argument 
are synchronized. 

## init

Specifies how the values of the matrix are initialized. Various init functions are available,
or you can load external data from CSV files. 

#### Position-based

* **rows**: elements in each row are initialized to the same value, with values spread evenly across a range specified 
  by **min** and **max** options. Set left init to rows
* **cols**: elements in each column are initialized to the same value, with values spread evenly across a range specified 
  by **min** and **max** options. Set right init to cols
* **row major**: elements are initialized from top left to bottom right in row major order, with values spread evenly across 
  a range specified by **min** and **max** options. Set left init to row major
* **col major**: elements are initialized from top left to bottom right in column major order, with values spread evenly across 
  a range specified by **min** and **max** options. Set right init to col major

#### Random

* **pt linear**: elements are drawn from a shape-dependent uniform distribution as described 
  [here](https://pytorch.org/docs/stable/generated/torch.nn.Linear.html).
  Set left and right init to pt linear
* **uniform**: elements are drawn from a uniform distribution as specified by **min** and **max** options.
  Set left and right init to uniform
* **gaussian**: elements are drawn from a gaussian distribution as specified by **min** and **max** options.
  Set left and right init to gaussian

#### Algebraic

* **tril mask**: lower triangular elements are initialized to one, others are initialized to zero.
  Set left init to tril mask
* **triu mask**: upper triangular elements are initialized to one, others are initialized to zero.
  Set left init to triu mask
* **eye**: elements on the diagonal are initialized to one, others are initialized to zero.
  Set left init to eye
* **diff**: elements on the diagonal are initialized to one; elements immediately left of the diagonal are initialized to -1, 
  all others are initialized to zero. Set left init to diff

#### Custom

* **url**: shows a **url** field which can be used to specify a URL pointing to CSV
  initialization data. Loaded data is consumed row by row, rolling over both columnwise and rowwise if
  matrix shape exceeds available data.
  Set left and right init to sample loaded weights
* **expr**: show an **expr** field which can be used to specify a Javascript initialization expression.
  Available variables are `i` (row index), `j` (column index), `h` (matrix height) and `w` (matrix width).

## dropout

Specifies a level of sparsity between 0 (0%) and 1 (100%) for row/col and random initializations. 
* Set left and right dropout to 0.5 (if applicable to current init choices)

## *Left/Right matmul options (matmul checked)*

When the **matmul** option is checked in the **left** and/or **right** submenu, the matrix options 
(h/w, init, etc.) are removed and matmul options are added: left/right sub-submenus, epilog, animation
and (depending on global options) layout.
      

#  
#  Animation

Various matmul algorithms can be animated. In a compound expression 
animation proceeds leaf-to-root in dependency order, with mutually independent
subexpressions proceeding in parallel. 

Algorithms are also parallelized within blocking 
partitions.

Fusion across matmuls occurs automatically as geometry permits - see the **fuse**
option below for details.

## alg

Specifies the matmul algorithm to be animated.

When a compound expression is animated, each child matmul chooses its own animation
algorithm - or chooses to inherit that of its parent - via an **animation** submenu. 

When a matmul specifies algorithm `none`, the expression tree rooted at that matmul 
is not animated: a choice of `none` at the top level disables animation globally, 
whereas `none` in a child disables animation of that subexpression.

* none: no animation of this matmul or its children
* dotprod (row major): elements of the result matrix are computed in **row major order** via **pairwise dot product**
* dotprod (col major): elements of the result matrix are computed in **column major order** via **pairwise dot product**
* axpy: columns of the result matrix are computed are computed by depthwise accumulation of **vector-scalar products**
* vmprod: rows of the result matrix are computed via **vector-matrix products** over rows of the left argument
* mvprod: columns of the result matrix are computed via **matrix-vector products** over columns of the right argument
* vvprod: the result matrix is computed via depthwise accumulation of **vector-vector outer products**
* **inherit** (child matmuls only): inherits the algorithm of its parent. This is the default setting for
  newly created child matmuls

## speed

Specifies animation speed. Values of this setting are not calibrated precisely: 1 is very slow and 100 
is essentally as fast as the browser can animate frames (for complicated visualizations, animation speed
will top out well before 100).

Note that animation speed is *not* calibrated to reflect the relative amounts of work performed: each
frame advances a single step, regardless of algorithm or argument shapes.

Choose an algorithm above and run it faster or slower. 

## pause

Pauses animation when checked.

## step

Advances paused animation one step. Useful for inspecting intermediate values in conjunction with
**interior spotlight** (see deco menu).

## fuse

In compound matmul expressions, particular combinations of adjacent planar algorithms 
(vector-matrix,
matrix-vector,
vector-vector)
can be **fused** when they generate parallel planes. 

Parallel planes visually indicate a shared *sweep axis* along which 
the data dependency between adjacent matmuls can be partitioned,
meaning the coplanar algorithms can be fused and parallelized.

(Partitions can be also visualized explicitly, irrespective of fusion, in the **blocking** submenu.)

### Fused pairs

The following combinations of two-matmul expression shape and algorithm generate parallel planes:

#### Left-associative: `A @ B @ C`

| `A @ B` (left child) | `_ @ C` (top level) | |
| - | - | - |
| vector-matrix product (fusion along **i**) | vector-matrix product (fusion along **i**) | Show |
| matrix-vector product (fusion along **k**) | vector-vector product (fusion along **j**) | Show |

#### Right-associative: `A @ (B @ C)`

| `B @ C` (right child) | `A @ _` (top level) | |
| - | - | - |
| vector-matrix product (fusion along **i**) | vector-vector product (fusion along **j**) | Show |
| matrix-vector product (fusion along **k**) | matrix-vector product (fusion along **k**) | Show |

### Fused chains

We can adjoin multiple pairs with common parallel planes to create extended fusions. Some examples:

* **`A @ B @ C @ ...`**: Generalizing the first left-associative pattern above, 
left-associative chains of any length can be fused along **i** (**vector-matrix** product).
Here the plane slicing through the compound corresponds to e.g. the path of computation for a single
batch item as it travels through an [MLP](https://pytorch.org/docs/stable/generated/torch.nn.Linear.html). 
This laminar geometry underlies [data parallelism](https://pytorch.org/docs/stable/generated/torch.nn.DataParallel.html)
(splitting a batch across multiple nodes):
  * Example: `X = A @ B @ C @ D @ E`
* **`A @ (B @ (C @ (...)))`**: Similarly, the second right-associative pattern above generalizes
to right-associative chains of any length fused along **k** (**matrix-vector** product). 
  * Example: `X = A @ (B @ (C @ (D @ E)))`
* **`(A @ B) @ (C @ D)`**: Binary expressions may be fused by computing the left subexpression along **k** 
(**matrix-vector** product) and the right subexpression along **i** (**vector-matrix** product), and joining them
along **j** (**vector-vector** product).
  * Example: `X = (A @ B) @ (C @ D)`
* **`(A @ (...)) @ ((...) @ Z)`**: More generally, binary expressions with a *right*-associative chain of arbitrary
length on the *left*, and a *left*-associative chain of arbitrary length on the *right*, may be fused into a single
unit by fusing the chained subexpressions as in the preceding examples, then joining them along **j** 
(**vector-vector** product) at the root.
  * Example: `X = (A @ (B @ C)) @ ((D @ E) @ F)`

### *sync vs async*

Options for **fuse** are `none` (no fusion), `sync` and `async`. The difference between `sync` and `async` is
subtle, and only apparent when large compound matmuls are animated. When **fuse** is set to `sync`, animations
are only fused when all participants begin can computation simultaneously (i.e., are not waiting for subcomputations 
to complete), whereas `async` animations will fuse even when participants begin at different times, dependency
order permitting.

For most expressions, `sync` and `async` will behave identically.

## hide inputs

Hiding inputs during animation can make it easier to inspect visualizations of intermediate results
rendered in the matmul cube's interior, in particular when **deco** menu options are adjusted to
minimize decoration and enable interior spotlighting (the latter reveals values in intermediate
visualizations - see **deco** for details).

## spin

Spinning a visualization can be useful in developing geometric intuition for the operations being visualized. 
* spin clockwise,
  spin counterclockwise 
* faster,
  slower,
  stop
      

#  
#  Blocking

Both simple and compound expressions can be partitioned into blocks in 3 dimensions. 
Partitions are *global*, in the sense that planes of partition cut across subexpressions,
representing parallelization of the entire compound expression.

The rules of partition propagation are straightforward (but note the subtlety around `k`):
* a partition along the `i` axis extends along contiguous chains of left arguments
* a partition along the `j` axis extends along contiguous chains of right arguments
* a partition along the `k` axis becomes a partition along the `j` axis for its left child,
  and a partition along the `i` axis for its right child (at which point it is subject to the `i`/`j` rules above)

Partitions in all dimensions can be freely mixed. 

Partitioning in each dimension corresponds to a different parallelization approach, with 
distinctive geometric properties. 
Animations are parallelized within the currently configured partitions.

Blocks are equal sized, with a short final block if the number of blocks is not an even divisor. 

## i blocks

Partitions the expression into the specified number of blocks along the **i** axis. 

**i** is the height dimension (rows) of the root matmul and its chain 
of left descendants. Partitioning it cuts the expression into horizontal slices within the
height bounds of the root matmul: i.e., the root matmul and its left descendants are 
partitioned, but not any matmul rooted in a right descendant.

Examples partitioned into 4 blocks along **i** 
(back to 1):
* X = A @ B (animate: 
  dotprod, 
  mvprod, 
  vmprod, 
  vvprod -
  faster, slower, stop)
* X = A @ B @ C (animate: 
  dotprod, 
  mvprod, 
  vmprod, 
  vvprod, 
  fused vmprod, 
  fused left mvprod/parent vvprod -
  faster, slower, stop)
* X = A @ (B @ C) (animate: 
  dotprod, 
  mvprod, 
  vmprod, 
  vvprod, 
  fused mvprod, 
  fused right vmprod/parent vvprod -
  faster, slower, stop)
* X = (A @ B) @ (C @ D) (animate: 
  dotprod, 
  mvprod, 
  vmprod, 
  vvprod, 
  fused left mvprod/right vmprod/parent vvprod -
  faster, slower, stop)

## k blocks

Partitions the expression into the specified number of blocks along the **k** axis. 

**k** is the matmul's "reduction" dimension, shared by the width of the left argument 
and height of the right argument.
Although not left- or right-transitive like partitions along **i** or **j** axes (respectively),
the geometry of partitioning along **k** is unique in extending to *both* left and right child 
matmuls via rotation:
* a partition along **k** in a parent becomes a partition along **j** in a left child
* a partition along **k** in a parent becomes a partition along **i** in a right child

Examples partitioned into 4 blocks along **j**
(back to 1):
* X = A @ B (animate: 
  dotprod, 
  mvprod, 
  vmprod, 
  vvprod -
  faster, slower, stop)
* X = A @ B @ C (animate: 
  dotprod, 
  mvprod, 
  vmprod, 
  vvprod, 
  fused vmprod, 
  fused left mvprod/parent vvprod -
  faster, slower, stop)
* X = A @ (B @ C) (animate: 
  dotprod, 
  mvprod, 
  vmprod, 
  vvprod, 
  fused mvprod, 
  fused right vmprod/parent vvprod -
  faster, slower, stop)
* X = (A @ B) @ (C @ D) (animate: 
  dotprod, 
  mvprod, 
  vmprod, 
  vvprod, 
  fused left mvprod/right vmprod/parent vvprod -
  faster, slower, stop)

## j blocks

Partitions the expression into the specified number of blocks along the **j** axis. 

**j** is the width dimension (columns) of the root matmul and its chain 
of right descendants. Partitioning it cuts the expression into vertical slices within the
width bounds of the root matmul: i.e., the root matmul and its right descendants are 
partitioned, but not any matmul rooted in a left descendant.

Examples partitioned into 4 blocks along **j**
(back to 1):
* X = A @ B (animate: 
  dotprod, 
  mvprod, 
  vmprod, 
  vvprod -
  faster, slower, stop)
* X = A @ B @ C (animate: 
  dotprod, 
  mvprod, 
  vmprod, 
  vvprod, 
  fused vmprod, 
  fused left mvprod/parent vvprod -
  faster, slower, stop)
* X = A @ (B @ C) (animate: 
  dotprod, 
  mvprod, 
  vmprod, 
  vvprod, 
  fused mvprod, 
  fused right vmprod/parent vvprod -
  faster, slower, stop)
* X = (A @ B) @ (C @ D) (animate: 
  dotprod, 
  mvprod, 
  vmprod, 
  vvprod, 
  fused left mvprod/right vmprod/parent vvprod -
  faster, slower, stop)

      

#  
# Layout

The layout submenu controls the arrangement of matmuls and their arguments in 3D space. 
Configuration options fall into two categories: **spacing** and **orientation**.

**Spacing** options influence the distance between elements in various ways. ``
The spacing options are **gap**, **scatter**, **molecule** and **blast**.

For many visualizations the default spacing settings will be fine, but for very deeply 
nested expressions - especially those saturated with both left and right subexpressions - 
tweaking these paramters can clarify the visualization and lead to new insights.

**Orientation** options control the placement of matmul arguments and result on the cube. 
**Polarity**, **left placement**, **right placement**
and **result placement** control the placement of parts of the root matmul, and **scheme**
controls how the placements of subexpressions evolve from the placement of their parents.

Here again, default settings are usually fine, but switching between different schemes 
can sometimes be quite useful in gaining intuition.

### *Spacing options*

## gap

The gap between the constituents of the matmul (left argument, right argument, result) along 
their shared edges. Unit distance is roughly the same as a single row or column. 
* increase gap, decrease gap

## scatter

Defines a fixed distance between child *matmuls* and their parents. (Simple child matrices are not scattered.)

Used in conjunction with **molecule** and **blast** to compute actual distances
used in visualizations; see below.
* example: using X = A @ B @ (C @ D) @ (E @ F @ (G @ H)) (or current visualization) 
increase scatter, decrease scatter

## molecule

A molecule is a child subexpression too large to bind tightly to its parent - i.e., the size at 
which **scatter** begins to apply (where a subexpression's size is the number of matmuls it contains).
* example using a combination of 
  large molecules and scatter to compactly visualize a deep, fully saturated expression
  without spatial collisions.

## blast

An exponential scaling term applied to **scatter** based on subexpression size (matmul count).

A blast value of zero leaves scatter constant; a positive value scatters larger subexpressions 
farther away from their parents - e.g., a blast of one multiplies scatter by subexpression size.
A negative blast value scatters smaller subexpressions farther away from their parents.

Positive blast can be useful for visualizing deep satarated trees, where it has 
an effect analogous to a 2D visualization in which lower levels of the tree
cluster together more closely.

* example: an alternate layout 
  for the **molecule** example above using less scatter, smaller molecules and a positive **blast** value.

Negative blast doesn't work that well with saturated, arboreal expressions but can be useful 
in visualizing mostly or entirely linear expressions using a layout with circular geometry 
(for example **wheel**, below). In those cases any nonzero blast value turns circles into 
spirals, with positive blast spiraling outward to the root matmul and negative blast spiraling 
inward.

### *Orientation options*

Before we get to the options themselves, some context:

#### Constraints on arrangement

Arranging a matmul (left argument, right argument, result) 
on 3 faces of a cube is subject to the following constraints (note: using "cube" 
here to mean "rectangular prism"):

* adjunction constraints:
  * left and right arguments must share a common edge, establishing the `k` axis in `i, k, j`
  * the result matrix must share an edge with the left argument, establishing the `i` axis
  * the result matrix must share an edge with the right argument, establishing the `j` axis
* orientation constraints:
  * the left argument's rows must run **parallel** to the `k` edge
  * the right argument's rows must run **perpendicular** to the `k` edge
  * the result matrix's rows must be coplanar with the rows of the left argument, 
    making its columns coplanar with the columns of the right argument

Visually this means we always cover 3 faces of the cube, contiguous around a
shared corner, with the row/column orientation of the faces subject to the above 
constraints.

We add an additional constraint here for familiarity: the left argument always 
occupies a vertical face of the cube representing the root matmul.
As a consequence, the right argument will always occupy a horizontal face, 
and the result matrix will also occupy a vertical face.

These constraints still leave room to maneuver. The space of valid arrangements 
can be parameterized by four orthogonal binary 
properties:  **polarity** (positive/negative), **left placement** (left/right), 
**right placement** (top/bottome) and **result placement** (front/back).
Details on each are below.

#### Subexpressions

The constraints and parameters described above are enough to visualize a single 
matmul, where the left and right arguments are matrices.
To visualize compound expressions, where arguments can themselves be matmuls,
we first need to adjoin child matmul cubes to their parents, then we need to
decide what the parameterization of the child cubes should be.

We have a natural constraint on how children are adjoined to parents: 
the face representing the child argument on the parent cube must also be the *result*
face of the child cube. 
Modulo this constraint, each child cube is free to choose a valid layout paramaterization.
Defining a rule for generating a child parameterization based on that of its parent
spares us having to hand-parameterize each matmul in a compound expression -
these rules are *schemes*.

## scheme

A *scheme* is a rule for choosing a child's layout based on the layout of its parent. 
Dfferent schemes produce distinctively different visualizations when iterated over the 
matmuls in a compound expression. 

Choose a compound matmul from elsewhere in this guide and then click on the links below 
to try alternate schemes. Remember that the final visualization depends heavily on
choice of initial placements - use links in those options below to try different
combinations.

* **blocks: the default scheme, which unfolds 
expressions as alternating convex and concave cubes. These visualizations are generally 
easy to interpret and robust to collisions up to quite large and saturated expressions. 
All visualizations in this guide default to the **blocks** scheme.
  * A @ B @ C @ D using block scheme and default placements
  (animate matrix-vector product, stop)
* **zigzag**: like the **blocks** scheme, this scheme 
uses alternation, but does not use alternating convexity and concavity. This can simplify
the flow of some visualizations, at the expense of greater occlusion:
  * A @ B @ C @ D using zigzag scheme and right placement at bottom
  (animate matrix-vector product, stop)
* **wheel**: simply rotates each child 90
degrees, which can produce intuitive circular visualizations for simple (sub)expressions 
but can be prone to spatial collisions (fixable with spacing). 
  * A @ B @ C @ D using wheel scheme with right placement at bottom
  (animate matrix-vector product, stop)
* custom: when this choice is selected
we apply no generative rule at all, but make layout parameters available
in all child submenus.

*(Note that spatial collisions are unavoidable in the general 
case, although schemes vary in their vulnerability to collisions and what expression
shapes produce them: in particular, the default **blocks** scheme doesn't normally 
produce collisions for expressions unless they are both saturated and more than 
3 generations deep. In any case, the spacing options above can be used to resolve 
collisions when they occur.)*

## polarity

Controls orientation of left and right arguments relative to the result matrix:
arguments have positive polarity when their normals point in the direction of
increase for their coplanar counterparts (rows for left, columns for right) 
in the result, and negative polarity when the normals point in the 
direction of decrease. 

E.g. When left and right arguments are placed as in the standard cube (left argument
on the left, right argument on top), negative polarity corresponds to the argument
faces "pointing outward," with their values reading left to right and top to bottom
in the usual way from a position outside the cube.

This orientation is visually indicated by the corner triangle in the *row guide*, 
positioned on the (0, 0) corner of the matrix.

## left placement

Controls whether the left argument is placed on the left or right face of the cube.        

## right placement

Controls whether the right argument is placed on the top or bottom face of the cube.        

## result placement

Controls whether the result matrix is placed on the front or back face of the cube.        

      

#  
# Deco

## legends

Controls the size of name/shape legends. (Also scaled by text and matrix size.) 0 removes them. 
* make legends bigger, smaller

## shape

When checked, shape legends are shown along the edges of input matrices. When unchecked, only name legends are shown. 
(When legends size is 0, neither are shown.)
* turn shapes on, off

## row guides

Controls the brightness of row guides superimposed over matrix values. 1 is maximum; 0 removes. 
* make row guides brighter, dimmer

## flow guides

Controls the brightness and size of flow guide arrows. 1 is maximum; 0 removes.
* make flow guides bigger and brighter, smaller and dimmer

## spotlight

Controls the size of the spotlight region in which matrix values are shown during **magnification** (see below).
* increase spotlight size, decrease it

## lens size

Controls the size of the **magnification** region (see below).
* increase lens size, decrease it

## magnification

Controls the magnification factor used when control-click, long click or long tap is used to display matrix values.
* increase magnification, decrease it

## interior spotlight

When checked, values are shown on the intermediate results in cube interiors during magnification.
* turn interior spotlight on, off

      

#  
# Colors and Sizes

## sensitivity

The size, brightness and color of a visualized matrix element depends on where its absolute value falls within a certain range.
Sensitivity controls how the range used for each value is constructed.

global sensitivity uses a single range for all values, from zero to
the global maximum absolute value present in the visualization. This produces a visualization in which value sizes,
brightnesses and colors are visually consistent, but small values can be faint in visualizations of data with 
high variance.

local sensitivity uses a separate comparison range for each matrix,
from zero to the maximum value present in that matrix. 
This increases the amount of visual information conveyed by visualizations with high variance, at the cost of global 
consistency.

superlocal goes one step further and instead of zero uses the 
minimum absolute value in the local matrix as its minimum. This can enhance visualizations of matrices whose values all lie within
a narrow band, far from zero.

semilocal uses a range from zero to the geomean of global and local
absolute maximum values.

## min size

The minimmum rendered size. (Values exactly equal to zero are not rendered.)
* increase minimum size, decrease minimum size

## min light

Minimum rendered brightness.
* increase minimum light, decrease minimum light

## max light

Maximum rendered brightness. 
(Note that values are rendered using the HSL color model, where hue converges to white as lightness approaches the maximum value of 1.)
* increase maximum light, decrease maximum light

## elem scale

Constant scaling factor applied to all elements.
* increase element scale, decrease element scale

## zero hue

Hue for zero values. Positive values have a higher hue value, negatives lower. (Note that hue values wrap around in the HSL model.)
* increase zero hue, decrease zero hue

## hue gap

Distance from zero hue at which value hues begin. A larger hue gap increases the color difference between positive and negative
values.
* increase hue gap, decrease hue gap

## hue spread

Rate at which hue changes based on value magnitude. 
* a hue spread of zero produces visualizations in which the same hue is used
for all positive and negative values respectively
* a small spread introduces small changes in hue based on magnitude, but keeps
positive and negative values distinguishable from each other 
* a large hue spread causes hue to change entirely as a function of
magnitude, and at the extreme (a spread value of 1) both positive and negative magnitude changes traverse the entire spectrum,
albeit from different directions        
* increase hue spread, decrease hue spread

      

#  
# Diag
    
## json
    
The parameters configuration object in JSON format.

## url
    
The URL containing the current configuration. This may be in compressed or uncompressed
form based on the `compressed` parameter property: uncompressed form is stringified JSON;
compressed is an internal representation.

## compressed

URL in unconditionally compressed form.
    
## geometries

three.js diagnostic: number of geometries currently in use.

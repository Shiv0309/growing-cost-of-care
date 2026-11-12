# growing-cost-of-care
A healthcare data engineering and visualization project exploring medication utilization and calculated uncovered costs using synthetic Synthea data.

## Colorblind-friendly chart palette

Use Okabe–Ito blue and orange for the two cost components. Keep their meanings consistent across charts.

| Color | Hex | Use |
| --- | --- | --- |
| Blue | `#0072B2` | Recorded payer coverage in stacked bars and payer points in the coverage scatter plot |
| Orange | `#E69F00` | Remaining medication cost after recorded payer coverage |
| Light gray | `#E8EDF1` | Shading for the pooled **All payer types** row and subtle gridlines |
| Slate gray | `#9AA7B2` | Dashed equal-coverage reference line in the scatter plot |
| Cool gray | `#CCD4DB` | Axis lines |
| Dark slate | `#182633` | Titles, annotations, and key values |
| Muted slate | `#52616E` | Tick labels and secondary text |
| White | `#FFFFFF` | Figure background |

Pair color with direct labels or a text legend. Use labels such as **No data** for missing groups so they are distinguishable from a measured **0%**. Use the gray band with a bold label to identify pooled results.

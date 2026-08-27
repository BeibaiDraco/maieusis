# Climate demo dataset notes

The climate demonstration ran against an ERA5-derived one-dimensional record of 60 degrees North
stratospheric dynamics. This page records what that dataset contains, what it cannot answer, and
what you would need to reproduce the run.

## What it is

A vertical column at a single latitude, resolved in height and time. It is designed for Northern
Hemisphere stratospheric variability, wave-mean-flow interaction, polar-vortex variability, and
sudden-warming-like events.

| Variable | Meaning |
| --- | --- |
| `fawa` | Finite-amplitude wave activity, a pseudomomentum density |
| `ubar` | Zonal-mean wind perturbation, used as a polar-vortex wind diagnostic |
| `uref` | Reference zonal wind, including radiative driving |
| `epz` | Eddy forcing related to the Eliassen-Palm flux, the lower-boundary forcing of the underlying one-dimensional model |

Three files carry the same four variables on the same grid:

| File | Dimensions | Contents |
| --- | --- | --- |
| `ana60n.nc` | height x time x month x year = 97 x 124 x 12 x 43 | Full analysis fields, including the seasonal cycle and interannual variability |
| `sea60n.nc` | height x time x month = 97 x 124 x 12 | Multi-year mean seasonal climatology, with no year dimension |
| `tran60n.nc` | height x time x month x year = 97 x 124 x 12 x 43 | Transient anomalies, `ana60n` minus `sea60n` |

`height` is 97 levels at 500 m spacing from 0 to 48 km. `time` is 124 sub-monthly steps,
corresponding to six-hourly data across 31 days. `year` spans approximately 1979 to 2021.
`sea60n` is approximately the multi-year mean of `ana60n` at each height, time slot, and month.

## What it cannot answer

These limits are properties of the data, not of the software, and they shaped every question the
run was able to accept:

- one latitude only, 60 degrees North;
- no longitude and no latitude dependence;
- no temperature, geopotential height, potential vorticity, topography, or surface variables.

So it cannot address regional wave sources, topographic forcing, surface impacts, blocking, or wave
phase structure. Several of the questions the run developed are explicitly bounded by this, and one
family was rejected on evidence grounds that trace back to it.

## Provenance and reproduction

The upstream source is ERA5 reanalysis, produced by the European Centre for Medium-Range Weather
Forecasts and distributed through the Copernicus Climate Change Service. ERA5 is publicly available
from Copernicus under its own licence and citation requirements; see
[the ECMWF dataset catalogue](https://www.ecmwf.int/en/forecasts/datasets).

**The one-dimensional derived product used here is not redistributed with this demonstration, and
the transformation that produces `fawa`, `ubar`, `uref`, and `epz` from ERA5 is not published as
part of it.** You can obtain ERA5 yourself, but you cannot rebuild these exact three files from
this repository alone. If you want to reproduce or extend the climate run, contact
`dracoxu@uchicago.edu`.

This is stated plainly rather than glossed: the neuroscience demonstrations point at versioned,
citable public datasets, and this one does not. The scientific artifacts are published in full
either way, and every claim in them is bounded by the limits listed above.

## Attribution

ERA5 data are generated using Copernicus Climate Change Service information and produced by ECMWF.
Neither the European Commission nor ECMWF is responsible for any use of the Copernicus information
or data it contains. See `THIRD_PARTY_NOTICES.md` in the repository root.

---

[Climate demo](README.md) · [All demo questions](../ALL_QUESTIONS.md)

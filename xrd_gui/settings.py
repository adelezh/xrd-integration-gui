from dataclasses import dataclass, asdict
from pathlib import Path
import json
import math

@dataclass(frozen=True)
class Settings:
    unit: str = '2th_deg'
    radial_bins: int = 5000
    azimuth_bins: int = 360
    radial_range: tuple | None = None
    sector: bool = False
    start: float = 100.
    end: float = 180.
    solid_angle: bool = True
    polarization: float = .99
    error_model: str = 'none'
    variance: str = ''
    compare_full: bool = False

    def validate(self):
        if self.unit not in ('2th_deg', 'q_A^-1'): raise ValueError('Choose 2theta or q units.')
        if not 1 <= self.radial_bins <= 100000 or not 1 <= self.azimuth_bins <= 10000:
            raise ValueError('Radial bins must be 1–100000; azimuth bins 1–10000.')
        if self.radial_bins * self.azimuth_bins > 20000000: raise ValueError('Reduce bins: maximum 20 million map cells.')
        if self.radial_range and (not all(math.isfinite(x) for x in self.radial_range) or not 0 <= self.radial_range[0] < self.radial_range[1]):
            raise ValueError('Radial range needs finite 0 <= minimum < maximum.')
        if not all(math.isfinite(x) for x in (self.start,self.end,self.polarization)): raise ValueError('Angles and polarization must be finite.')
        if not -1 <= self.polarization <= 1: raise ValueError('Polarization must be between -1 and 1.')
        if self.sector and (not -180 <= self.start <= 180 or not -180 <= self.end <= 180 or self.start == self.end):
            raise ValueError('Sector angles must be different, within -180 to 180 degrees.')
        if self.error_model not in ('none','poisson','supplied'): raise ValueError('Unsupported uncertainty model.')
        if self.error_model == 'supplied' and not self.variance: raise ValueError('Choose a variance image (variance, not sigma).')
        return self

class Preferences:
    def __init__(self, path=None):
        self.path = Path(path or Path.home() / '.xrd_tk_settings.json')
        try: self.data = json.loads(self.path.read_text())
        except (OSError, ValueError): self.data = {}
    def save(self):
        self.path.write_text(json.dumps(self.data, indent=2))
    def remember(self, key, path):
        self.data[key] = str(path)
        if key == 'workspace':
            self.data['recent'] = list(dict.fromkeys([str(path)] + self.data.get('recent', [])))[:10]
        self.save()

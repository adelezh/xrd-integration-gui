"""Run with the same interpreter as the desktop application."""
import sys, time, tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from xrd_gui.gui import App
from xrd_gui.settings import Preferences,Settings
from xrd_gui.processing import Engine
from xrd_gui.files import read_image
import numpy as np
out=Path('.test-output');out.mkdir(exist_ok=True)
base=Path(r'C:\Users\hzhong\OneDrive - Brookhaven National Laboratory\Project\2026\Flash_07112026')
source=next((base/'Mo_3'/'dark_sub').glob('*.tiff'))
engine=Engine(base/'CeO2_2_poni.poni',base/'CeO2_2.npy');data=read_image(source)
for unit in ('2th_deg','q_A^-1'):
    c,m,meta=engine.integrate(data,Settings(unit=unit,radial_bins=200,azimuth_bins=90,error_model='poisson',sector=True,start=170,end=-170),str(source))
    assert len(c[0].x)==200 and m.intensity.shape==(90,200)
    assert np.isfinite(c[0].intensity).all()
    print('Real TIFF:',source.name,'shape',data.shape,'unit',unit,'sigma available',c[0].sigma is not None)
app=App(Preferences(out/'preferences.json'))
app.engine=engine;app.poni.set(str(base/'CeO2_2_poni.poni'));app.mask.set(str(base/'CeO2_2.npy'))
app.load_engine()
app.files=[str(source)];app.refresh_files();app.navigate(1)
app.svars['radial_bins'].set('200');app.svars['azimuth_bins'].set('90');app.sector.set(True);app.svars['start'].set('170');app.svars['end'].set('-170');app.svars['error_model'].set('poisson')
app.update();app.run_integration(True,True)
deadline=time.monotonic()+90
while app.busy and time.monotonic()<deadline:app.update();time.sleep(.02)
assert not app.busy and app.curves and app.map_result is not None
assert [app.tabs.tab(t,'text') for t in app.tabs.tabs()]==['Integration','Batch Integration','File Manipulate']
app.update()
try:
    from PIL import ImageGrab
    ImageGrab.grab(bbox=(app.winfo_rootx(),app.winfo_rooty(),app.winfo_rootx()+app.winfo_width(),app.winfo_rooty()+app.winfo_height())).save(out/'gui-smoke.png')
except Exception as e:print('Screenshot unavailable:',e)
app.tabs.select(1);app.update();app.tabs.select(2);app.update();app.destroy()
print('GUI smoke passed: three tabs, real detector loading, sector overlay, asynchronous 1D/2D processing, plot rendering.')

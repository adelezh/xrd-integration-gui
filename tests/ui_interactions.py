"""GUI worker and snapshot regression checks on the local display."""
import sys,time,json,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from unittest.mock import patch
from xrd_gui.gui import App
from xrd_gui.settings import Preferences
from xrd_gui.files import read_curve
out=Path('.test-output/ui-jobs');out.mkdir(parents=True,exist_ok=True)
app=App(Preferences(out/'prefs.json'));app.geometry('1280x800+10+10');failures=[]
app.error=lambda e,detail='':failures.append(str(e))
base=Path(r'C:\Users\hzhong\OneDrive - Brookhaven National Laboratory\Project\2026\Flash_07112026');source=next((base/'AIC3_6'/'dark_sub').glob('*00001.tiff'))
steps=[];wait_start=None

def setup():
    app.poni.set(str(base/'CeO2_2_poni.poni'));app.mask.set(str(base/'CeO2_2.npy'));app.load_engine();app.cal_fold.set_open(False)
    app.files=[str(source)];app.refresh_files();app.navigate(1);app.svars['radial_bins'].set('120');app.svars['azimuth_bins'].set('36')
    # The real detector has masked empty edge bins; export a populated range.
    app.svars['minimum'].set('1');app.svars['maximum'].set('10')
    app.run_integration(True,True);assert app.busy

def diagnostic_finished():
    assert app.curves and app.map_result is not None
    assert app.result_status.get()=='1D ready | 2D ready'
    app.svars['radial_bins'].set('121');assert app.result_status.get()=='1D outdated | 2D outdated'
    app.tabs.select(1);app.batch_files=[str(source)];app.bvars['folder'].set(str(out/'batch'));app.bvars['policy'].set('Unique name');app.capture_batch()
    assert app.batch_settings.radial_bins==121
    app.start_batch();assert app.busy
    app.svars['radial_bins'].set('122');assert app.batch_settings.radial_bins==121
    assert str(app.batch_format.cget('state'))=='disabled'

def batch_finished():
    rows=app.batch_preview.tree.get_children();assert len(rows)==1
    assert 'Saved:' in app.batch_preview.tree.item(rows[0],'values')[-1]
    products=list((out/'batch').glob('*.xy'));assert products
    assert len(read_curve(products[-1]).x)==121
    app.tabs.select(2);app.manip_files=[str(products[-1])];app.operation.set('For TOPAS');app.mvars['folder'].set(str(out/'topas'));app.mvars['policy'].set('Unique name');app.mvars['naming'].set('Keep original');app.mvars['extension'].set('.xye');app.approx.set(True);app.mvars['scale'].set('2');app.input_changed('manip')
    app.start_manip();assert app.busy

def topas_finished():
    assert 'Saved:' in app.manip_preview.tree.item('0','values')[-1]
    assert list((out/'topas').glob('*.xye'))
    # Confirm launch still uses a nonblocking subprocess and the active TIFF.
    with patch('importlib.util.find_spec',return_value=object()),patch('subprocess.Popen') as launch:
        app.calibrate();args,kwargs=launch.call_args;assert args[0][-1]==str(source);assert '-m' in args[0]
    app.save_panel_sizes();assert 'panels' in json.loads((out/'prefs.json').read_text())
    assert not failures,failures
    print('GUI worker checks passed: diagnostic updates, fixed batch snapshot, per-product status, TOPAS conversion, nonblocking calibration command, pane persistence.',flush=True)
    app.destroy()
steps=[setup,diagnostic_finished,batch_finished,topas_finished]
def tick():
    global wait_start
    if app.busy:
        if wait_start is None:wait_start=time.monotonic()
        if time.monotonic()-wait_start>90:raise RuntimeError('Worker timed out')
        app.after(100,tick);return
    wait_start=None
    try:
        if failures:raise AssertionError(failures)
        steps.pop(0)()
    except Exception:
        traceback.print_exc();app.destroy();sys.exit(1)
    if steps:app.after(300,tick)
app.after(700,tick);app.mainloop()

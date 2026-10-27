"""Method state, comparison, persistence and invalidation GUI checks."""
import sys,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from PIL import ImageGrab
from xrd_gui.gui import App
from xrd_gui.settings import Preferences
from xrd_gui.processing import Engine,StableAzimuthalIntegrator
out=Path('.test-output/methods');out.mkdir(parents=True,exist_ok=True)
app=App(Preferences(out/'prefs.json'));app.geometry('1920x1080+0+0')
app.prefs.data.pop('integration_methods',None)
errors=[];app.error=lambda e,detail='':errors.append((str(e),detail))
ai=StableAzimuthalIntegrator(dist=.1,poni1=.0064,poni2=.0064,pixel1=.0001,pixel2=.0001,wavelength=1e-10)
p=out/'synthetic.poni';ai.save(str(p));app.engine=Engine(p)
y,x=np.indices((128,128));r=np.hypot(x-63.5,y-63.5);im=30+80*np.exp(-((r-38)/3)**2);im[60:65,22:27]+=4000
app.image_data=im;app.active='Synthetic rings and spots';app.cal_fold.set_open(False);app.settings_fold.set_open(True)
app.svars['radial_bins'].set('24');app.svars['azimuth_bins'].set('24');app.svars['error_model'].set('poisson')
steps=[]
def state(label):
    app.settings_fold.set_open(True);app.method_display.set(label);app.compare_average.set(True);app.method_vars['sigma_threshold'].set('5');app.method_vars['percentile_low'].set('25');app.method_vars['percentile_high'].set('75');app.settings_scroll.canvas.yview_moveto(0)
    s=app.settings();app.curves,app.map_result,app.map_meta=app.engine.integrate(im,s,'Synthetic rings and spots')
    app.curve_revision=app.revision_1d;app.map_revision=app.revision_2d
    app.draw_detector();app.draw_curves();app.draw_map();app.refresh_result_status()
    if label!='Average':assert len(app.curves)==2 and app.curve_ax.lines[1].get_linestyle()=='--'
    assert len(app.tabs.tabs())==3
    assert bool(app.method_area.winfo_manager()) == (label!='Average')

def capture(label):
    app.lift();app.attributes('-topmost',True);app.update()
    import ctypes
    ctypes.windll.user32.RedrawWindow(app.winfo_id(),None,None,0x185)
    app.update()
    x,y=app.winfo_rootx(),app.winfo_rooty()
    ImageGrab.grab(bbox=(x,y,x+app.winfo_width(),y+app.winfo_height())).save(out/(label+'.png'))
    app.attributes('-topmost',False)

def checks():
    app.percentile_preset.set('Median');app.apply_percentile_preset();assert app.settings().percentile_argument==50
    app.method_vars['percentile_low'].set('26.5');assert app.percentile_preset.get()=='Custom'
    assert app.result_status.get()=='1D outdated | 2D ready'
    app.method_vars['sigma_threshold'].set('invalid');assert app.settings().method_1d=='percentile'
    app.method_display.set('Average');assert app.settings().sigma_threshold==5
    app.method_display.set('Sigma-clipping')
    try:app.settings()
    except ValueError:pass
    else:raise AssertionError('Invalid threshold accepted')
    assert app.settings(False).method_1d=='average'
    app.method_vars['sigma_threshold'].set('3');app.method_display.set('Percentile filtering')
    app.capture_batch();frozen=app.batch_settings;app.method_vars['percentile_low'].set('29');assert frozen.percentile_low==26.5
    app.persist_methods();app.svars['azimuth_bins'].set('30');assert app.result_status.get()=='1D outdated | 2D outdated'
    assert not errors,errors
    print('Method GUI checks passed; screenshots in',out,flush=True);app.destroy()
for name in ['Average','Sigma-clipping','Percentile filtering']:
    steps.extend([lambda name=name:state(name),lambda name=name:capture(name)])
steps.extend([lambda:app.settings_fold.set_open(False),lambda:capture('comparison-overlay')])
steps.append(checks)
def tick():
    try:steps.pop(0)()
    except Exception:traceback.print_exc();app.destroy();sys.exit(1)
    if steps:app.after(500,tick)
app.after(500,tick);app.mainloop()

"""Interactive-layout smoke checks; screenshots are generated, never user data writes."""
import sys, json, traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from xrd_gui.gui import App
from xrd_gui.settings import Preferences,Settings
from xrd_gui.files import read_image,Curve,write_curve
from xrd_gui.processing import Engine
from PIL import ImageGrab

out=Path('.test-output/ui');out.mkdir(parents=True,exist_ok=True)
app=App(Preferences(out/'prefs.json'));app.geometry('1280x800+10+10')
errors=[]
def error(exc,detail=''):
    errors.append(str(exc));print('UI ERROR:',exc,detail,flush=True)
app.error=error
steps=[]
def capture(name):
    app.update_idletasks()
    import ctypes
    ctypes.windll.user32.RedrawWindow(app.winfo_id(),None,None,0x185)
    x,y=app.winfo_rootx(),app.winfo_rooty()
    ImageGrab.grab(window=app.winfo_id()).save(out/(name+'.png'))
    print('Captured',name,flush=True)
def select(index):app.tabs.select(index)
for i,name in enumerate(['integration','batch','manip']):
    steps.extend([lambda i=i:select(i),lambda name=name:capture('1280-empty-'+name)])
base=Path(r'C:\Users\hzhong\OneDrive - Brookhaven National Laboratory\Project\2026\Flash_07112026')
source=next((base/'AIC3_6'/'dark_sub').glob('*00001.tiff'))
def populate():
    app.tabs.select(0);app.poni.set(str(base/'CeO2_2_poni.poni'));app.mask.set(str(base/'CeO2_2.npy'));app.load_engine();app.cal_fold.set_open(False)
    app.files=[str(source),str(source).replace('00001.tiff','00000.tiff')];app.refresh_files();app.navigate(1)
    app.file_tree.selection_set('0','1');app.select_file();assert len(app.selected_files())==2
    app.filter.set('00001');assert len(app.selected_files())==1;app.filter.set('');app.file_tree.selection_set('0','1')
    app.svars['radial_bins'].set('500');app.svars['azimuth_bins'].set('90')
    app.curves,app.map_result,app.map_meta=app.engine.integrate(app.image_data,app.settings(),str(source))
    before=app.map_result.intensity.copy();app.draw_curves();app.draw_map();app.map_scale.set('Log');app.draw_map();np.testing.assert_array_equal(app.map_result.intensity,before);app.reset_map_display()
    app.result_status.set('Results ready');app.batch_files=app.files.copy();app.bvars['folder'].set(str(out/'batch'));app.capture_batch();assert len(app.batch_preview.tree.get_children())==2
    # Source curves with and without sigma exercise TOPAS controls without detector text parsing.
    for index,sigma in [(0,None),(1,np.ones(3))]:
        p=out/f'Curve_{index}_20260711-134044_fb35z4_primary-1_mean_tth.xy'
        if not p.exists():write_curve(p,Curve(np.arange(3.),np.ones(3),sigma,{'unit':'2th_deg'}))
    app.manip_files=[str(p) for p in out.glob('Curve*.xy')];app.mvars['folder'].set(str(out/'manip'));app.input_changed('manip')
    app.operation.set('For TOPAS');app.mvars['extension'].set('.xye');app.mvars['scale'].set('3');app.approx.set(True);app.update_idletasks();assert app.approx_widget.winfo_manager()=='grid'
    app.operation.set('Average');assert app.manip_values()[0]['scale']==1 and app.manip_values()[3] is False
    app.operation.set('For TOPAS');assert app.mvars['scale'].get()=='3';app.mvars['extension'].set('.xy');assert not app.approx_widget.winfo_manager();assert not app.manip_values()[3]
    app.operation.set('Average');app.mvars['folder'].set(str(out/'manip'));app.preview_manip();assert len(app.manip_preview.tree.get_children())==1
    app.manip_preview.tree.item('0',open=True)
    print('Selection, independent map display, preview, operation persistence and isolation checks passed',flush=True)
steps.append(populate)
for i,name in enumerate(['integration','batch','manip']):steps.extend([lambda i=i:select(i),lambda name=name:capture('1280-populated-'+name)])
steps.append(lambda:app.geometry('1920x1080+0+0'))
for i,name in enumerate(['integration','batch','manip']):steps.extend([lambda i=i:select(i),lambda name=name:capture('1920-populated-'+name)])
def finish():
    assert not errors,errors
    app.tabs.select(0);app.toggle_files();app.toggle_files();app.clear();assert not app.files
    print('UI checks passed. Tk scaling:',app.tk.call('tk','scaling'),flush=True);app.destroy()
def show_advanced():
    app.tabs.select(0);app.settings_fold.set_open(True);app.advanced_fold.set_open(True)
    app.update_idletasks()
    panel=app.settings_fold.body.winfo_children()[0];panel.canvas.yview_moveto(1)
def show_topas():
    app.tabs.select(2);app.operation.set('For TOPAS');app.mvars['extension'].set('.xye');app.approx.set(True)
    panel=app.manip_controls.master.master;panel.canvas.yview_moveto(.55)
def show_copy():
    app.tabs.select(2);app.operation.set('Copy / Rename');app.mvars['naming'].set('Custom')
    panel=app.manip_controls.master.master;panel.canvas.yview_moveto(.4)
steps.extend([show_advanced,lambda:capture('1920-advanced'),show_topas,lambda:capture('1920-topas'),show_copy,lambda:capture('1920-copy-custom')])
steps.append(finish)
def next_step():
    if not steps:return
    try:steps.pop(0)()
    except Exception:
        traceback.print_exc();app.destroy();sys.exit(1)
    if steps:app.after(600,next_step)
app.after(800,next_step);app.mainloop()

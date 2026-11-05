from pathlib import Path
import sys, json, traceback
from lupa.lua51 import LuaRuntime
ROOT=Path(__file__).resolve().parents[1]
EXTRA=r'''
local methods=getmetatable(plate).__index
function methods:GetFrameLevel()return self.level or 1 end
function methods:SetFrameLevel(v)self.level=v end
Minimap=CreateFrame('Frame','Minimap',UIParent);Minimap.width=140;Minimap.height=140
cursorX=500;cursorY=200
function GetCursorPosition()return cursorX,cursorY end

function methods:SetHeight(v)self.height=v end
function methods:SetScale(v)self.scale=v end
function methods:SetJustifyH(v)self.justifyH=v end
function methods:SetColorTexture(...)self.color={...}end
function methods:SetOrientation(v)self.orientation=v end
function methods:SetMinMaxValues(a,b)self.min=a;self.max=b end
function methods:SetValueStep(v)self.step=v end
function methods:SetObeyStepOnDrag(v)self.obey=v end
function methods:SetThumbTexture(v)self.thumb=self:CreateTexture();self.thumb:SetTexture(v)end
function methods:GetThumbTexture()return self.thumb end
function methods:SetValue(v)self.value=v;if self.scripts.OnValueChanged then self.scripts.OnValueChanged(self,v)end end
function methods:GetValue()return self.value end
function methods:SetChecked(v)self.checked=v end
function methods:GetChecked()return self.checked end
for _,k in ipairs({'EnableMouse','SetMovable','SetClampedToScreen','RegisterForDrag','StartMoving','StopMovingOrSizing'})do methods[k]=function()end end

function methods:SetAlpha(v)assert(not self.secure,'Only artwork may fade');self.alpha=v end
function methods:SetVertexColor(r,g,b)self.tint={r,g,b}end
function methods:SetNormalTexture(v)self.normal=self.normal or self:CreateTexture();self.normal:SetTexture(v)end
function methods:GetNormalTexture()return self.normal end
function methods:SetHighlightTexture(v)self.highlight=self.highlight or self:CreateTexture();self.highlight:SetTexture(v)end
function methods:GetHighlightTexture()return self.highlight end
function methods:SetBlendMode(v)self.blend=v end
function methods:GetCenter()return self.cx or 400,self.cy or 200 end
function methods:GetRight()return self.right or 500 end
function methods:GetEffectiveScale()return self.scale or 1 end
function methods:GetHeight()return self.height or 32 end
function methods:GetWidth()return self.width or 200 end
plates={nameplate1=plate};casts={};hover='nameplate1'
C_NamePlate.GetNamePlateForUnit=function(u)return plates[u]end
function UnitIsUnit(a,b)return a=='mouseover'and b==hover end
function UnitCastingInfo(u)return casts[u]end
function UnitChannelInfo()end
function addplate(u)
 local root=CreateFrame('Frame',u,UIParent);local hb=CreateFrame('Frame',nil,root)
 root.UnitFrame={healthBar=hb};plates[u]=root;return root
end
function event(e,arg)if P.frame.events[e]then P.frame.scripts.OnEvent(nil,e,arg)end end
function tick()P.frame.scripts.OnUpdate(nil,.2)end
function bar()return P.bars[plate]end
'''
def runtime(pre=None):
    lua=LuaRuntime(unpack_returned_tuples=True)
    lua.execute((ROOT/'tools/mock.lua').read_text()+EXTRA)
    if pre: lua.execute(pre)
    p=lua.table(); loader=lua.eval('function(s,p)assert(loadstring(s))("CounterCast",p)end')
    for file in [line.strip() for line in (ROOT/'CounterCast/CounterCast.toc').read_text().splitlines() if line.strip().endswith('.lua')]:
        loader((ROOT/'CounterCast'/file).read_text(),p)
    lua.globals().P=p;lua.execute("if not skipLoad then event('ADDON_LOADED','CounterCast')end")
    return lua,p
results=[]
def test(name,code,pre=None):
    try:
        lua,p=runtime(pre);lua.execute(code);results.append(dict(name=name,passed=True))
    except Exception as e:
        traceback.print_exc();results.append(dict(name=name,passed=False,error=str(e)))

test('Automatic startup prepares buttons without a probe command',"tick();assert(bar().prepared and #bar().buttons==2 and macroCreates==2)")
test('Right root anchor is centered with the health bar and matches its thickness',"tick();local b=bar().buttons[1];assert(b.parent==plate and b.points[1][1]=='RIGHT'and b.points[1][2]==plate and b.points[1][3]=='RIGHT');assert(b.points[1][4]==-2 and b.points[1][5]==0 and b.width==32 and b.height==32)")
test('Scaled geometry uses screen coordinates while retaining root anchoring',"health.scale=.8;plate.scale=1.2;health.right=600;plate.right=400;health.cy=330;plate.cy=200;health.height=48;tick();local x,y,size=P:Geometry(plate,2);assert(math.abs(x+2)<.001 and math.abs(y-20)<.001 and math.abs(size-32)<.001)")
test('Unavailable health geometry has a larger 28 pixel fallback',"plate.UnitFrame=nil;tick();assert(bar().size==28 and bar().buttons[1].points[1][5]==0)")
test('Restricted health geometry is not used',"health.GetHeight=function()return {secret=true}end;tick();assert(bar().size==28)")
test('Narrow plate fits all buttons in its native region',"health.width=64;tick();assert(bar().size==29);assert(bar().buttons[2].points[1][4]==-33)")
test('Multiple plates share character macros and retain fixed spell order',"local r=addplate('nameplate2');tick();assert(P.bars[r].prepared and macroCreates==2);assert(P.bars[r].buttons[1].attributes.macro==bar().buttons[1].attributes.macro)")
test('Exact saved mouseover macro has no target changes or fallback',"tick();for _,row in ipairs(P.rows)do local _,_,body=GetMacroInfo(row.macro);assert(body=='/cast [@mouseover,harm,nodead] '..row.name)end")
test('Native click handler and release behavior are preserved',"tick();local b=bar().buttons[1];assert(b.scripts.OnClick==SecureActionButton_OnClick and b.attributes.useOnKeyDown==false);assert(b.clickTypes[1]=='LeftButtonDown'and b.clickTypes[2]=='LeftButtonUp');assert(b.motionEnabled==false and b.clickEnabled==true and b.propagateMotion==true and b.propagateClicks==false)")
test('Cooldown priority advances without combat attribute writes',"tick();combat=true;cooldowns[6552]={startTime=10,duration=10,isEnabled=true};casts.nameplate1='Fireball';tick();assert(bar().buttons[1].count.text=='10'and bar().buttons[1].ready.text=='');assert(bar().buttons[2].ready.text=='>'and bar().buttons[2].glow.alpha==1);assert(bar().buttons[1].attributes.macro==P.rows[1].macro)")
test('Unknown cooldown is never promoted to ready',"tick();combat=true;cooldowns[6552]={startTime={secret=true},duration=10,isEnabled=true};tick();assert(bar().buttons[1].count.text=='?'and bar().buttons[1].ready.text=='')")
test('Restricted cast and identity observations do not block visual updates',"tick();combat=true;UnitCastingInfo=function()return {secret=true}end;UnitIsUnit=function()return {secret=true}end;tick();assert(bar().buttons[1].glow.alpha==0)")
test('Cooldown reads are shared across nameplates',"addplate('nameplate2');tick();local n=0;local old=P.Cooldown;P.Cooldown=function(...)n=n+1;return old(...)end;tick();assert(n==2)")
test('New native root created during combat is deferred safely',"tick();local r=addplate('nameplate2');combat=true;event('NAME_PLATE_CREATED',r);event('NAME_PLATE_UNIT_ADDED','nameplate2');tick();assert(P.pending and not P.bars[r].prepared and #P.bars[r].buttons==0);combat=false;event('PLAYER_REGEN_ENABLED');assert(P.bars[r].prepared)")
test('Prepared native root can recycle in combat without reconfiguration',"tick();combat=true;event('NAME_PLATE_UNIT_REMOVED','nameplate1');plates.nameplate1=nil;plates.nameplate2=plate;event('NAME_PLATE_UNIT_ADDED','nameplate2');tick();assert(bar().unit=='nameplate2'and bar().prepared and not P.units.nameplate1)")
test('Removed units do not retain visible-unit bookkeeping',"tick();combat=true;event('NAME_PLATE_UNIT_REMOVED','nameplate1');assert(not bar().unit and not P.units.nameplate1)")
test('Rebuild clears stale mappings',"tick();plates.nameplate1=nil;P:Rebuild();assert(not bar().unit and not next(P.units))")
test('Unannounced mapping mismatch suppresses readiness claims',"tick();combat=true;plates.nameplate1=nil;tick();assert(bar().buttons[1].ready.text==''and bar().buttons[1].count.text==''and bar().buttons[1].icon.alpha==0 and bar().buttons[1].glow.alpha==0)")
test('Friendly units receive no ready or cast highlight',"tick();combat=true;UnitCanAttack=function()return false end;tick();assert(bar().buttons[1].ready.text==''and bar().buttons[1].glow.alpha==0)")
test('Off outside combat clears secure actions',"tick();SlashCmdList.COUNTERCAST('off');assert(not P.appliedEnabled and not bar().buttons[1].shown and not bar().buttons[1].attributes.type)")
test('Combat settings defer every protected mutation',"tick();combat=true;SlashCmdList.COUNTERCAST('off');tick();assert(P.pending and P.appliedEnabled and bar().buttons[1].shown);combat=false;event('PLAYER_REGEN_ENABLED');assert(not P.appliedEnabled and not bar().buttons[1].shown)")
test('Size controls persist and apply after combat',"tick();combat=true;SlashCmdList.COUNTERCAST('size 40');assert(bar().size==32);combat=false;event('PLAYER_REGEN_ENABLED');assert(bar().size==40);SlashCmdList.COUNTERCAST('size auto');assert(bar().size==32)")
test('Invalid sizes leave the current setting intact',"tick();SlashCmdList.COUNTERCAST('size 999');assert(P.db.size==0);SlashCmdList.COUNTERCAST('size nope');assert(P.db.size==0)")
test('Learned ranks refresh only after combat',"tick();combat=true;known[1672]=true;event('SPELLS_CHANGED');tick();assert(P.rows[2].id==72);combat=false;event('PLAYER_REGEN_ENABLED');assert(P.rows[2].id==1672 and macroCreates==2)")
test('Controls can be disabled without inventing a Paladin interrupt',"tick();assert(#P.rows==1);SlashCmdList.COUNTERCAST('controls off');assert(#P.rows==0 and not bar().buttons[1].shown)","class='PALADIN';known={[5588]=true}")
test('Unavailable mouse APIs fail closed',"tick();assert(P.lastError and not bar().prepared);for _,b in ipairs(frames)do if b.secure then assert(not b.shown and not b.attributes.type)end end", "getmetatable(plate).__index.SetMouseMotionEnabled=nil")
test('Rejected attachment clears all active actions',"tick();assert(P.lastError and not bar().prepared);for _,b in ipairs(bar().buttons)do assert(not b.shown and not b.attributes.type)end", "rejectAnchor=true")
test('Forbidden roots are skipped',"tick();assert(not P.bars[plate])", "plate.forbidden=true")
test('Missing nameplate APIs do not prevent load',"tick();assert(not next(P.bars))", "C_NamePlate=nil")
test('Full macro slots do not overwrite user macros or arm partial actions',"tick();assert(P.lastError and #P.rows==0 and macroCreates==0);assert(macros[121].body=='/say mine')", "for i=121,138 do macros[i]={name='User '..i,body='/say mine'}end")
test('Partially available macro capacity never partially arms the bar',"tick();assert(#P.rows==0 and not bar());assert(macroCreates==1)", "for i=121,137 do macros[i]={name='User '..i,body='/say mine'}end")
test('User-edited owned macro is preserved',"tick();macros[121].body='/say mine';P:Rebuild();assert(macros[121].body=='/say mine'and macroCreates==3 and P.rows[1].macro~='CounterCast 1')")
test('Duplicate macro names are not reused',"tick();macros[1]={name=P.rows[1].macro,body='/say mine'};P:Rebuild();assert(P.rows[1].macro~='CounterCast 1'and macros[1].body=='/say mine')")
test('Probe ownership is copied and validated before reuse',"tick();assert(macroCreates==1 and P.rows[1].macro=='CCP Cast 1');assert(P.characterDB.ownedMacros~=CounterCastProbeCharacterDB.ownedMacros)", "macros[121]={name='CCP Cast 1',body='/cast [@mouseover,harm,nodead] Spell 6552'};CounterCastProbeCharacterDB={ownedMacros={{name=macros[121].name,body=macros[121].body}}}")
test('Truncated macro readback never arms',"tick();assert(P.lastError and #P.rows==0)", "local old=CreateMacro;CreateMacro=function(n,i,b,c)return old(n,i,b:sub(1,12),c)end")
test('Repeated refresh does not duplicate buttons or macros',"tick();local n=#frames;for i=1,10 do P:Rebuild()end;assert(#frames==n and macroCreates==2 and macroEdits==0)")
test('Mouseover observations never invoke native casting themselves',"tick();combat=true;local b=bar().buttons[1];b.scripts.PreClick(b,'LeftButton',true);assert(not P.lastClick);b.scripts.PreClick(b,'LeftButton',false);assert(P.lastClick.matched);P:Status()")
test('Startup in combat defers macros and secure creation',"tick();assert(not next(P.bars)and macroCreates==0);combat=false;event('PLAYER_REGEN_ENABLED');assert(bar().prepared)", "combat=true")
test('No abilities means no fabricated button',"tick();assert(#P.rows==0 and not bar().prepared and #bar().buttons==0)", "known={}")
test('Existing probe is disarmed during initialization',"assert(disarmed)", "CounterCastProbe={Disarm=function()disarmed=true end}")
for cls,spell in [('WARRIOR',72),('ROGUE',1766),('MAGE',2139),('SHAMAN',8042),('DRUID',5211),('HUNTER',19503),('PALADIN',853),('PRIEST',15487),('WARLOCK',19244)]:
    test(cls+' learned ability discovery',f"tick();assert(#P.rows==1 and P.rows[1].id=={spell})", f"class='{cls}';known={{[{spell}]=true}};petKnown={{[{spell}]=true}}")
test('Pet interrupt requires a learned pet spell',"tick();assert(#P.rows==0)", "class='WARLOCK';known={[19244]=true}")
test('Racial control appears only when learned',"tick();assert(#P.rows==1 and P.rows[1].id==20549)","class='MAGE';known={[20549]=true}")
test('Disabled cooldown stays unknown and elapsed cooldown becomes ready',"cooldowns[72]={startTime=10,duration=10,isEnabled=false};assert(P:Cooldown(72)==nil);cooldowns[72].isEnabled=true;uptime=21;assert(P:Cooldown(72)==0)")
test('Global cooldown is excluded from spell cooldown indicator',"cooldowns[72]={startTime=10,duration=1.5,isEnabled=true,isOnGCD=true};assert(P:Cooldown(72)==0)")
test('Spell names containing macro syntax cannot arm actions',"tick();assert(P.lastError and #P.rows==0 and macroCreates==0)","C_Spell.GetSpellInfo=function()return {name='Kick\\n/targetenemy'}end")


# Strict startup tests: the original mock accepted every event name.
reject_legacy="local m=getmetatable(plate).__index;local old=m.RegisterEvent;m.RegisterEvent=function(self,e)if e=='LEARNED_SPELL_IN_TAB'then error('Unknown event: '..e)end;old(self,e)end"
test('Client rejecting obsolete learned-spell event still loads and draws first plate',"assert(P.initialized and type(SlashCmdList.COUNTERCAST)=='function');assert(not P.frame.events.LEARNED_SPELL_IN_TAB);tick();assert(bar().prepared);SlashCmdList.COUNTERCAST('status')",reject_legacy)
test('Rejected optional event cannot abort handler or command registration',"tick();assert(P.initialized and bar().prepared and P.unavailableEvents[1]=='NAME_PLATE_CREATED');assert(P.frame.events.UNIT_PET);SlashCmdList.COUNTERCAST('status');local found=false;for _,msg in ipairs(messages)do if msg:find('Unavailable events: NAME_PLATE_CREATED',1,true)then found=true end end;assert(found)","local m=getmetatable(plate).__index;local old=m.RegisterEvent;m.RegisterEvent=function(self,e)if e=='NAME_PLATE_CREATED'then error('Unsupported event')end;old(self,e)end")
test('Every event registers after handlers and slash command exist',"tick();assert(bar().prepared and #P.unavailableEvents==0 and P.frame.events.ADDON_LOADED and P.frame.events.UNIT_PET)","local m=getmetatable(plate).__index;local old=m.RegisterEvent;m.RegisterEvent=function(self,e)assert(self.scripts.OnEvent and self.scripts.OnUpdate and SlashCmdList.COUNTERCAST);old(self,e)end")
test('Initialization emits a versioned load confirmation once',"local n=#messages;P:Initialize();assert(#messages==n and messages[1]:find(P.version..' loaded.',1,true))")
test('Login initializes if addon-loaded delivery was missed',"assert(not P.initialized);event('PLAYER_LOGIN');tick();assert(P.initialized and bar().prepared)","skipLoad=true")
test('World entry initializes if startup event delivery was missed',"assert(not P.initialized);event('PLAYER_ENTERING_WORLD');tick();assert(P.initialized and bar().prepared)","skipLoad=true")
test('First nameplate appearing after startup attaches through its event',"plates.nameplate1=nil;tick();assert(not next(P.bars));plates.nameplate1=plate;event('NAME_PLATE_UNIT_ADDED','nameplate1');assert(bar().prepared)")


test('Ready cast stays fully colored in combat',"tick();combat=true;casts.nameplate1='Fireball';tick();local b=bar().buttons[1];assert(b.icon.alpha==1 and not b.icon.desaturated and b.icon.tint[2]==1 and b.normal.alpha==1 and b.highlight.alpha==1)")
test('Idle enemy fades all button art without hiding the secure action',"tick();combat=true;tick();local b=bar().buttons[1];assert(b.shown and b.attributes.type=='macro'and b.icon.alpha==.15 and b.normal.alpha==.15 and b.highlight.alpha==.15 and b.ready.text==''and b.glow.alpha==0)")
test('Cooldown fades in combat and recovers when ready during casting',"tick();combat=true;casts.nameplate1='Fireball';cooldowns[6552]={startTime=10,duration=10,isEnabled=true};tick();local b=bar().buttons[1];assert(b.icon.alpha==.15 and b.count.text=='10'and b.count.alpha==.45);uptime=21;tick();assert(b.icon.alpha==1 and b.count.text==''and not b.icon.desaturated)")
test('Unknown combat cooldown preserves color without claiming ready',"tick();combat=true;casts.nameplate1='Fireball';cooldowns[6552]={startTime={secret=true},duration=10,isEnabled=true};tick();local b=bar().buttons[1];assert(b.icon.alpha==1 and b.icon.tint[2]==1 and not b.icon.desaturated and b.ready.text==''and b.count.text=='?')")
test('Unknown casting does not masquerade as idle',"tick();combat=true;UnitCastingInfo=function()return {secret=true}end;tick();assert(bar().buttons[1].icon.alpha==1 and bar().buttons[1].glow.alpha==0)")
test('Channels receive the same full-color emphasis',"tick();combat=true;UnitChannelInfo=function()return 'Channel'end;tick();assert(bar().buttons[1].icon.alpha==1 and bar().buttons[1].glow.alpha==1)")
test('Known out-of-range is red and not selected as ready',"tick();combat=true;casts.nameplate1='Fireball';C_Spell.IsSpellInRange=function(id,u)assert(u=='nameplate1');return id~=6552 end;tick();local b=bar().buttons[1];assert(b.icon.alpha==1 and b.icon.tint[1]==1 and b.icon.tint[2]==.18 and b.ready.text=='');assert(bar().buttons[2].ready.text=='>')")
test('Returning in range restores normal color',"tick();combat=true;casts.nameplate1='Fireball';C_Spell.IsSpellInRange=function()return false end;tick();C_Spell.IsSpellInRange=function()return true end;tick();assert(bar().buttons[1].icon.tint[2]==1)")
test('Unknown and secret range never become red',"tick();combat=true;casts.nameplate1='Fireball';C_Spell.IsSpellInRange=function()return {secret=true}end;tick();assert(bar().buttons[1].icon.tint[2]==1);C_Spell.IsSpellInRange=function()error('Restricted')end;tick();assert(bar().buttons[1].icon.tint[2]==1)")
test('Legacy range uses localized name and supports numeric result',"tick();IsSpellInRange=function(n,u)assert(n=='Spell 6552'and u=='nameplate1');return 0 end;assert(P:Range(P.rows[1],'nameplate1')==false)")
test('Range alias must be the same nameplate enemy',"tick();C_Spell.IsSpellInRange=function(id,u)if u=='target'then return false end end;UnitIsUnit=function()return false end;assert(P:Range(P.rows[1],'nameplate1')==nil);UnitIsUnit=function(a,b)return a=='target'and b=='nameplate1'end;assert(P:Range(P.rows[1],'nameplate1')==false)")
test('Mailbox root without an enemy never receives a button',"tick();local mailbox=CreateFrame('Frame',nil,UIParent);event('NAME_PLATE_CREATED',mailbox);assert(#P.bars[mailbox].buttons==0 and not P.bars[mailbox].prepared);P:Rebuild();assert(#P.bars[mailbox].buttons==0)")
test('Friendly or interactable units are not armed',"UnitCanAttack=function()return false end;tick();assert(not bar().prepared and #bar().buttons==0 and not P.lastError)")
test('Unit removal clears every visual immediately during combat',"tick();combat=true;casts.nameplate1='Fireball';tick();event('NAME_PLATE_UNIT_REMOVED','nameplate1');local b=bar().buttons[1];assert(b.icon.alpha==0 and b.normal.alpha==0 and b.highlight.alpha==0 and b.count.alpha==0 and b.glow.alpha==0 and not bar().enemy);assert(b.shown and b.attributes.type=='macro')")
test('Removed enemy detaches outside combat to prevent mailbox clicks',"tick();event('NAME_PLATE_UNIT_REMOVED','nameplate1');local b=bar().buttons[1];assert(not b.shown and not b.attributes.type and b.parent==UIParent)")
test('Reused root for a friendly clears artwork without combat mutation',"tick();combat=true;event('NAME_PLATE_UNIT_REMOVED','nameplate1');UnitCanAttack=function()return false end;event('NAME_PLATE_UNIT_ADDED','nameplate1');tick();assert(bar().buttons[1].icon.alpha==0 and not bar().enemy)")
test('Confirmed enemy with restricted reaction retains casting visuals',"tick();combat=true;casts.nameplate1='Fireball';UnitCanAttack=function()return {secret=true}end;tick();assert(bar().buttons[1].icon.alpha==1)")


test('Upgrade preserves layout and opacity defaults',"tick();assert(P.db.offsetX==0 and P.db.offsetY==0 and P.db.idleAlpha==.15 and P.db.cooldownAlpha==.15 and P.db.castGlow==true and bar().size==32)")
test('Bare slash command opens reusable nonsecure menu',"tick();SlashCmdList.COUNTERCAST('');local f=P.options;assert(f and f.shown and not f.secure and f.auto.checked and f.glow.checked);assert(f.idleAlpha.value==15 and f.cooldownAlpha.value==15 and f.offsetX.value==0);local n=#frames;SlashCmdList.COUNTERCAST('options');assert(#frames==n)")
test('Size slider sets custom size and updates real geometry',"tick();P:OpenOptions();P.options.size:SetValue(40);tick();assert(P.db.size==40 and bar().size==40 and not P.options.auto.checked)")
test('Auto checkbox restores exact previous default anchor geometry',"tick();P:OpenOptions();P.options.size:SetValue(40);P.options.auto:SetChecked(true);P.options.auto.scripts.OnClick(P.options.auto);tick();assert(P.db.size==0 and bar().size==32 and bar().buttons[1].points[1][4]==-2 and bar().buttons[1].points[1][5]==0)")
test('Offsets add to measured root anchor',"tick();P:OpenOptions();P.options.offsetX:SetValue(12);P.options.offsetY:SetValue(-8);tick();assert(bar().buttons[1].points[1][4]==10 and bar().buttons[1].points[1][5]==-8)")
test('Combat menu applies opacity and glow immediately, layout after combat',"tick();combat=true;casts.nameplate1='Fireball';P:OpenOptions();P.options.size:SetValue(44);P.options.offsetX:SetValue(20);P.options.cooldownAlpha:SetValue(30);P.options.glow:SetChecked(false);P.options.glow.scripts.OnClick(P.options.glow);cooldowns[6552]={startTime=10,duration=10,isEnabled=true};tick();assert(bar().size==32 and bar().buttons[1].points[1][4]==-2 and bar().buttons[1].icon.alpha==.3 and bar().buttons[2].glow.alpha==0);combat=false;event('PLAYER_REGEN_ENABLED');assert(bar().size==44 and bar().buttons[1].points[1][4]==18)")
test('Idle and cooldown opacity are independent; fainter wins when both apply',"tick();P:SetAppearance('idleAlpha',.6);P:SetAppearance('cooldownAlpha',.2);tick();assert(bar().buttons[1].icon.alpha==.6);cooldowns[6552]={startTime=10,duration=10,isEnabled=true};tick();assert(bar().buttons[1].icon.alpha==.2);casts.nameplate1='Fireball';tick();assert(bar().buttons[1].icon.alpha==.2 and bar().buttons[2].icon.alpha==1)")
test('Zero opacity clears all artwork but preserves secure action',"tick();combat=true;P:SetAppearance('idleAlpha',0);local b=bar().buttons[1];assert(b.icon.alpha==0 and b.normal.alpha==0 and b.highlight.alpha==0 and b.count.alpha==0 and b.attributes.type=='macro'and b.shown)")
test('Glow toggle preserves ready marker and tint',"tick();casts.nameplate1='Fireball';P:SetAppearance('castGlow',false);tick();assert(bar().buttons[1].glow.alpha==0 and bar().buttons[1].ready.text=='>'and bar().buttons[1].icon.tint[2]==1);P:SetAppearance('castGlow',true);assert(bar().buttons[1].glow.alpha==1)")
test('Preview and menu reflect saved values without changing macros',"tick();local n=macroCreates;P:OpenOptions();P.options.idleAlpha:SetValue(42);P.options.cooldownAlpha:SetValue(5);assert(P.options.previews[2].icon.alpha==.42 and P.options.previews[3].icon.alpha==.05 and macroCreates==n)")
test('Appearance reset preserves enable/control preference',"tick();P.db.controls=false;P.db.enabled=false;P:OpenOptions();P:SetAppearance('offsetX',30);P:SetAppearance('idleAlpha',.7);P:ResetAppearance();assert(P.db.enabled==false and P.db.controls==false and P.db.offsetX==0 and P.db.size==0 and P.db.castGlow and P.db.idleAlpha==.15)")
test('Menu close and Escape registration are scoped to this menu',"tick();P:OpenOptions();assert(UISpecialFrames[1]=='CounterCastOptions');P.options.close.scripts.OnClick();assert(not P.options.shown and bar().buttons[1].shown)")
test('Saved appearance values persist across initialization',"tick();assert(P.db.size==40 and P.db.offsetX==9 and P.db.offsetY==-4 and P.db.idleAlpha==.3 and P.db.cooldownAlpha==.7 and not P.db.castGlow)","CounterCastDB={size=40,offsetX=9,offsetY=-4,idleAlpha=.3,cooldownAlpha=.7,castGlow=false}")
test('Invalid saved appearance values revert individually',"tick();assert(P.db.offsetX==0 and P.db.offsetY==0 and P.db.idleAlpha==.15 and P.db.cooldownAlpha==.15 and P.db.castGlow)","CounterCastDB={offsetX=999,offsetY=-999,idleAlpha=-1,cooldownAlpha='bad',castGlow='yes'}")
test('Invalid option input cannot corrupt saved state',"tick();P:SetAppearance('idleAlpha',2);P:SetAppearance('offsetX',math.huge);P:SetAppearance('other',2);assert(P.db.idleAlpha==.15 and P.db.offsetX==0 and P.db.other==nil)")


test('Minimap launcher appears automatically with left click only',"assert(P.minimapButton and P.minimapButton.shown and not P.minimapButton.secure and P.minimapButton.parent==Minimap);assert(P.minimapButton.clickTypes[1]=='LeftButtonUp'and P.db.minimapAngle==225)")
test('Minimap click opens existing options without changing enablement',"tick();local b=P.minimapButton;b.scripts.OnClick(b,'LeftButton');assert(P.options.shown and P.db.enabled);local n=#frames;b.scripts.OnClick(b,'LeftButton');assert(#frames==n)")
test('Minimap options remain usable in combat',"tick();combat=true;P.minimapButton.scripts.OnClick(P.minimapButton,'LeftButton');assert(P.options.shown and bar().prepared)")
test('Minimap drag saves position and suppresses release click',"tick();local b=P.minimapButton;b.scripts.OnMouseDown(b);b.scripts.OnDragStart(b);b.scripts.OnUpdate(b,.2);b.scripts.OnDragStop(b);assert(P.db.minimapAngle==0 and not b.scripts.OnUpdate);b.scripts.OnClick(b,'LeftButton');assert(not P.options);b.scripts.OnMouseDown(b);b.scripts.OnClick(b,'LeftButton');assert(P.options.shown)")
test('Minimap drag converts scaled cursor coordinates',"Minimap.scale=2;cursorX=800;cursorY=600;P:DragMinimap();assert(P.db.minimapAngle==90 and math.abs(P.minimapButton.points[1][4])<.001 and P.minimapButton.points[1][5]==78)")
test('Saved minimap angle survives startup and resizing',"assert(P.db.minimapAngle==90);Minimap.width=200;Minimap.height=200;Minimap.scripts.OnSizeChanged(Minimap);assert(P.minimapButton.points[1][5]==108)","CounterCastDB={minimapAngle=90}")
test('Invalid minimap angle falls back without changing appearance',"assert(P.db.minimapAngle==225 and P.db.size==40)","CounterCastDB={minimapAngle=0/0,size=40}")
test('Square minimap positioning follows its edge',"P.db.minimapAngle=45;P:PositionMinimap();assert(math.abs(P.minimapButton.points[1][4]-78)<.001 and math.abs(P.minimapButton.points[1][5]-78)<.001)","GetMinimapShape=function()return 'SQUARE'end")
test('Late minimap creation retries at world entry',"assert(not P.minimapButton and P.initialized);Minimap=CreateFrame('Frame','Minimap',UIParent);event('PLAYER_ENTERING_WORLD');assert(P.minimapButton and P.minimapButton.shown)","Minimap=nil")
test('Launcher failure does not abort startup or slash options',"tick();assert(P.initialized and bar().prepared);SlashCmdList.COUNTERCAST('options');assert(P.options.shown)","Minimap.GetFrameLevel=function()error('Unsupported launcher API')end")
test('Minimap tooltip identifies the addon and cleans up on leave',"local b=P.minimapButton;b.scripts.OnEnter(b);assert(GameTooltip.text=='CounterCast'and GameTooltip.shown);b.scripts.OnLeave(b);assert(not GameTooltip.shown)")
test('Repeated login never duplicates the minimap button',"local b=P.minimapButton;local n=#frames;event('PLAYER_LOGIN');event('PLAYER_ENTERING_WORLD');assert(P.minimapButton==b and #frames==n)")


test('Hidden combat timer with active flag honors zero cooldown opacity',"tick();P:SetAppearance('cooldownAlpha',0);combat=true;casts.nameplate1='Fireball';cooldowns[6552]={startTime={secret=true},duration={secret=true},isEnabled=true,isActive=true};tick();local b=bar().buttons[1];assert(b.icon.alpha==0 and b.normal.alpha==0 and b.highlight.alpha==0 and b.count.alpha==0 and b.glow.alpha==0 and b.ready.text=='');assert(P.cooldownStatus[6552].active==true and P.cooldownStatus[6552].source=='activity flag')")
test('Hidden timer honors nonzero cooldown opacity exactly',"tick();P:SetAppearance('cooldownAlpha',.37);combat=true;casts.nameplate1='Fireball';cooldowns[6552]={startTime={secret=true},duration={secret=true},isEnabled=true,isActive=true};tick();assert(bar().buttons[1].icon.alpha==.37 and bar().buttons[1].count.text=='')")
test('Hidden timer with inactive flag restores color and readiness',"tick();combat=true;casts.nameplate1='Fireball';cooldowns[6552]={startTime={secret=true},duration={secret=true},isEnabled=true,isActive=false};tick();assert(bar().buttons[1].icon.alpha==1 and bar().buttons[1].ready.text=='>')")
test('Active flag countdown expiry restores icon without leaving combat',"tick();P:SetAppearance('cooldownAlpha',0);combat=true;casts.nameplate1='Fireball';cooldowns[6552]={startTime={secret=true},duration={secret=true},isActive=true};tick();assert(bar().buttons[1].icon.alpha==0);cooldowns[6552].isActive=false;tick();assert(bar().buttons[1].icon.alpha==1)")
test('Active cooldown and idle opacity combine using fainter preference',"tick();P:SetAppearance('cooldownAlpha',.6);P:SetAppearance('idleAlpha',.2);combat=true;cooldowns[6552]={startTime={secret=true},duration={secret=true},isActive=true};tick();assert(bar().buttons[1].icon.alpha==.2)")
test('Native duration activity works when timing and flag are restricted',"tick();combat=true;casts.nameplate1='Fireball';P:SetAppearance('cooldownAlpha',0);cooldowns[6552]={startTime={secret=true},duration={secret=true},isActive={secret=true}};C_Spell.GetSpellCooldownDuration=function(id,ignoreGCD)assert(ignoreGCD==true);return {IsActive=function()return id==6552 end}end;tick();assert(bar().buttons[1].icon.alpha==0 and bar().buttons[2].ready.text=='>');assert(P.cooldownStatus[6552].source=='native duration')")
test('Native duration zero fallback excludes global cooldown',"tick();combat=true;casts.nameplate1='Fireball';cooldowns[6552]={startTime={secret=true},duration={secret=true},isActive=true};C_Spell.GetSpellCooldownDuration=function(id,ignoreGCD)assert(ignoreGCD==true);return {IsZero=function()return true end}end;tick();assert(bar().buttons[1].icon.alpha==1 and bar().buttons[1].ready.text=='>')")
test('Nonzero native duration fades without readable seconds',"tick();P:SetAppearance('cooldownAlpha',0);combat=true;casts.nameplate1='Fireball';cooldowns[6552]={startTime={secret=true},duration={secret=true}};C_Spell.GetSpellCooldownDuration=function()return {IsZero=function()return false end}end;tick();assert(bar().buttons[1].icon.alpha==0 and bar().buttons[1].count.text=='')")
test('Restricted native duration result falls back to plain activity flag',"tick();cooldowns[6552]={startTime={secret=true},duration={secret=true},isActive=true};C_Spell.GetSpellCooldownDuration=function()return {IsActive=function()return {secret=true}end,IsZero=function()return {secret=true}end}end;local remaining,active=P:Cooldown(6552);assert(remaining==nil and active==true)")
test('Rejected native duration API does not break plain cooldown path',"tick();cooldowns[6552]={startTime={secret=true},duration={secret=true},isActive=true};C_Spell.GetSpellCooldownDuration=function()error('Unavailable API')end;local remaining,active=P:Cooldown(6552);assert(remaining==nil and active==true)")
test('Secret active flag is never interpreted as false or true',"tick();cooldowns[6552]={startTime={secret=true},duration={secret=true},isActive={secret=true}};local remaining,active=P:Cooldown(6552);assert(remaining==nil and active==nil)")
test('Cooldown opacity slider still applies while combat timer is hidden',"tick();combat=true;casts.nameplate1='Fireball';cooldowns[6552]={startTime={secret=true},duration={secret=true},isActive=true};P:OpenOptions();P.options.cooldownAlpha:SetValue(0);assert(bar().buttons[1].icon.alpha==0);P.options.cooldownAlpha:SetValue(60);assert(bar().buttons[1].icon.alpha==.6)")
test('Real native cooldown overrides stale GCD-only numeric reading',"tick();cooldowns[6552]={startTime=10,duration=1.5,isEnabled=true,isOnGCD=true};C_Spell.GetSpellCooldownDuration=function()return {IsActive=function()return true end}end;local remaining,active=P:Cooldown(6552);assert(remaining==nil and active==true)")
test('Status reports activity source without disclosing secret timing',"tick();cooldowns[6552]={startTime={secret=true},duration={secret=true},isActive=true};tick();P:Status();local found=false;for _,msg in ipairs(messages)do if msg:find('cooldown active (activity flag)',1,true)then found=true end end;assert(found)")
test('Native duration can report ready when numeric API is unavailable',"C_Spell.GetSpellCooldown=function()return nil end;C_Spell.GetSpellCooldownDuration=function()return {IsZero=function()return true end}end;local remaining,active=P:Cooldown(6552);assert(remaining==0 and active==false)")

lua,p=runtime("class='PALADIN';known={[5588]=true}");lua.execute('tick()')
b=lua.eval('bar().buttons[1]')
snapshot={'version':p.version,'source':'Lua 5.1 mocked runtime, not a game screenshot','anchor':b.points[1][1], 'relativeAnchor':b.points[1][3], 'x':b.points[1][4], 'y':b.points[1][5], 'width':b.width,'height':b.height,'healthWidth':200,'healthHeight':32,'macro':lua.eval('macros[121].body')}
(ROOT/'docs/layout.json').write_text(json.dumps(snapshot,indent=2)+'\n')
states=[]
for label,setup in [('Casting / ready',"casts.nameplate1='Fireball'"),('Casting / out of range',"casts.nameplate1='Fireball';C_Spell.IsSpellInRange=function()return false end"),('Not casting',''),('Cooldown',"casts.nameplate1='Fireball';cooldowns[5588]={startTime=10,duration=10,isEnabled=true}")]:
    l,statep=runtime("class='PALADIN';known={[5588]=true}");l.execute('tick();combat=true;'+(setup+';' if setup else '')+'tick()')
    button=l.eval('bar().buttons[1]')
    states.append({'label':label,'alpha':button.icon.alpha,'tint':[button.icon.tint[i] for i in (1,2,3)],'desaturated':button.icon.desaturated,'count':button.count.text,'countAlpha':button.count.alpha,'ready':button.ready.text,'glow':button.glow.alpha})
(ROOT/'docs/visual-states.json').write_text(json.dumps({'source':'Actual Lua mock visual outputs; not native rendering','states':states},indent=2)+'\n')

l,op=runtime();l.execute('tick();P:OpenOptions()')
panel=op.options
(ROOT/'docs/options-layout.json').write_text(json.dumps({'width':panel.width,'height':panel.height,'defaults':{k:op.db[k] for k in ['size','offsetX','offsetY','idleAlpha','cooldownAlpha','castGlow']},'sliderPositions':{k:{'x':panel[k].points[1][4],'y':-panel[k].points[1][5],'value':panel[k].value,'min':panel[k].min,'max':panel[k].max} for k in ['size','offsetX','offsetY','idleAlpha','cooldownAlpha']},'source':'Lua mock widget geometry; schematic only'},indent=2)+'\n')
l,mp=runtime()
button=mp.minimapButton
(ROOT/'docs/minimap-layout.json').write_text(json.dumps({'source':'Lua mock geometry; not an in-game screenshot','angle':mp.db.minimapAngle,'buttonSize':button.width,'x':button.points[1][4],'y':button.points[1][5],'minimapSize':140,'icon':button.icon.texture},indent=2)+'\n')
l,cp=runtime("class='PALADIN';known={[5588]=true}")
l.execute("tick();P:SetAppearance('cooldownAlpha',0);combat=true;casts.nameplate1='Fireball';cooldowns[5588]={startTime={secret=true},duration={secret=true},isActive=true};tick()")
button=l.eval('bar().buttons[1]')
regression={'scenario':'Combat; enemy casting; cooldown opacity 0%; numeric timer restricted; isActive true','fixedIconAlpha':button.icon.alpha,'fixedBorderAlpha':button.normal.alpha,'fixedHighlightAlpha':button.highlight.alpha,'fixedCountdownAlpha':button.count.alpha,'fixedGlowAlpha':button.glow.alpha,'source':cp.cooldownStatus[5588].source,'remainingSecondsKnown':False}
(ROOT/'docs/combat-opacity.json').write_text(json.dumps(regression,indent=2)+'\n')
test('Full character macro cache restores icons across fifty rebuilds',"tick();assert(#P.rows==1 and bar().prepared and bar().buttons[1].shown and P.lastError==nil);for i=1,50 do P:Rebuild();tick()end;assert(macroCreates==0 and macroEdits==0 and bar().prepared);assert(bar().buttons[1].attributes.macro=='CounterCast 1')","Constants={MacroConsts={MAX_ACCOUNT_MACROS=120,MAX_CHARACTER_MACROS=30}};class='DRUID';known={[20549]=true};C_Spell.GetSpellInfo=function()return {name='War Stomp',iconID=20549}end;for i=121,150 do macros[i]={name='Preserved '..i,body='/say keep'}end;macros[149]={name='CounterCast 1',body='/cast [@mouseover,harm,nodead] War Stomp'..string.char(10)};CounterCastCharacterDB={ownedMacros={{name='CounterCast 1',body='/cast [@mouseover,harm,nodead] War Stomp'}}}")

test('New spell choices preserve every default',"tick();assert(#P.rows==2 and not next(P.db.disabledSpells));P:OpenSpellOptions();assert(P.spellOptions.rows[1].checked and P.spellOptions.rows[2].checked)")
test('Disabled families leave only selected secure actions',"tick();P:SetSpellSelected(6552,false);tick();assert(#P.rows==1 and P.rows[1].id==72 and bar().buttons[1].row.id==72);assert(not bar().buttons[2].shown and not bar().buttons[2].attributes.type)")
test('New ranks keep the spell family disabled',"tick();P:SetSpellSelected(72,false);known[1672]=true;event('SPELLS_CHANGED');tick();assert(#P.rows==1 and P.rows[1].id==6552);P:SetSpellSelected(72,true);assert(P.rows[2].id==1672)")
test('Saved family selections survive initialization',"tick();assert(#P.rows==1 and P.rows[1].id==72)","CounterCastDB={disabledSpells={['6552']=true}}")
test('Combat selection does not mutate protected actions or macros',"tick();local macro=bar().buttons[1].attributes.macro;local edits=macroEdits;combat=true;P:OpenSpellOptions();P:SetSpellSelected(6552,false);tick();assert(P.pending and P.dirty and #P.rows==2 and bar().buttons[1].attributes.macro==macro and macroEdits==edits);assert(P.spellOptions.notice.text:find('after combat'));combat=false;event('PLAYER_REGEN_ENABLED');assert(#P.rows==1 and P.rows[1].id==72)")
test('Select none clears all active buttons out of combat',"tick();P:SelectClassSpells(false);assert(#P.rows==0 and not bar().prepared and not bar().buttons[1].shown);P:SelectClassSpells(true);assert(#P.rows==2 and bar().prepared)")
test('Combat select none keeps actions until combat ends',"tick();combat=true;P:SelectClassSpells(false);tick();assert(#P.rows==2 and bar().prepared);combat=false;event('PLAYER_REGEN_ENABLED');assert(#P.rows==0 and not bar().buttons[1].shown)")
test('Choices cannot grant unlearned spells',"tick();P:SelectClassSpells(true);assert(#P.rows==2);P:OpenSpellOptions();assert(not P:SpellChoices('WARRIOR')[3].known and P.spellOptions.rows[3].detail.text:find('Not learned'))")
test('Pet ability filtering preserves pet-known checks',"tick();assert(#P.rows==1 and P.rows[1].pet);P:SetSpellSelected(19244,false);assert(#P.rows==0);P:SetSpellSelected(19244,true);assert(#P.rows==1)","class='WARLOCK';known={};petKnown={[19647]=true}")
test('Racial selection follows family ID',"tick();assert(#P.rows==3);P:SetSpellSelected(20549,false);assert(#P.rows==2)","known[20549]=true")
test('Current-class selection does not overwrite another class',"tick();P:SelectClassSpells(true);assert(P.db.disabledSpells['1766']==true)","CounterCastDB={disabledSpells={['1766']=true}}")
test('Malformed saved selections normalize safely',"tick();assert(type(P.db.disabledSpells)=='table' and #P.rows==2)","CounterCastDB={disabledSpells='bad'}")
test('Appearance reset does not reset spell choices',"tick();P:SetSpellSelected(6552,false);P:ResetAppearance();tick();assert(not P:IsSpellSelected(6552) and #P.rows==1)")
test('Controls toggle remains compatible with individual choices',"tick();P:OpenSpellOptions();P.spellOptions.controls:SetChecked(false);P.spellOptions.controls.scripts.OnClick(P.spellOptions.controls);assert(#P.rows==0 and P:IsSpellSelected(853));P.spellOptions.controls:SetChecked(true);P.spellOptions.controls.scripts.OnClick(P.spellOptions.controls);assert(#P.rows==1)","class='PALADIN';known={[5588]=true}")
test('Options navigation reuses windows and closes correctly',"tick();P:OpenOptions();P.options.spells.scripts.OnClick();assert(P.spellOptions.shown and not P.options.shown);local count=#frames;P:OpenSpellOptions();assert(#frames==count);P.spellOptions.done.scripts.OnClick();assert(P.options.shown and not P.spellOptions.shown);SlashCmdList.COUNTERCAST('spells');P.spellOptions.close.scripts.OnClick();assert(not P.spellOptions.shown)")
test('Spell checkbox changes its own family',"tick();P:OpenSpellOptions();local b=P.spellOptions.rows[2];b:SetChecked(false);b.scripts.OnClick(b);assert(P:IsSpellSelected(6552) and not P:IsSpellSelected(72) and #P.rows==1)")
test('Unknown family changes are ignored',"tick();P:SetSpellSelected(999999,false);assert(not next(P.db.disabledSpells) and #P.rows==2)")
for className in ['WARRIOR','ROGUE','MAGE','SHAMAN','DRUID','HUNTER','PALADIN','PRIEST','WARLOCK']:
    test('Spell menu covers '+className,"tick();P:OpenSpellOptions();local choices=P:SpellChoices(class);assert(#choices==#P.abilities[class]+1);for i,r in ipairs(choices)do assert(P.spellOptions.rows[i].family==r.family and P.spellOptions.rows[i].shown)end",f"class='{className}';known={{}}")

report={'version':p.version,'passed':sum(r['passed'] for r in results),'total':len(results),'nativeOverlayUserConfirmed':True,'automaticLifecycleLiveVerified':False,'checks':results}
(ROOT/'docs/verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(f"{report['passed']}/{report['total']} Lua 5.1 checks passed")
sys.exit(0 if all(r['passed'] for r in results) else 1)

local _,P=...
local function combat()return InCombatLockdown and InCombatLockdown()end
local defaults={size=0,customSize=32,offsetX=0,offsetY=0,idleAlpha=.15,cooldownAlpha=.15,castGlow=true}
local limits={size={16,64},offsetX={-100,100},offsetY={-80,80},idleAlpha={0,1},cooldownAlpha={0,1}}
function P:SetAppearance(key,value)
 if not self.initialized then return end
 if key=='castGlow'then
  if type(value)~='boolean'then return end
 else
  local range=limits[key]
  if not range or not self:IsPlain(value)or type(value)~='number'or value~=value then return end
  if not(key=='size'and value==0)and (value<range[1]or value>range[2])then return end
 end
 if self.db[key]==value then return end
 self.db[key]=value
 if key=='size'and value>0 then self.db.customSize=value end
 if key=='size'or key=='offsetX'or key=='offsetY'then
  -- Coalesce slider movement; never touch protected layout while in combat.
  self.dirty=true;if combat()then self.pending=true end
 else self:Update()end
 if self.options then self:RefreshOptions()end
end
function P:ResetAppearance()
 for key,value in pairs(defaults)do self.db[key]=value end
 self.dirty=true;if combat()then self.pending=true end
 self:Update();self:RefreshOptions()
end
local function label(parent,value,x,y,font)
 local t=parent:CreateFontString(nil,'OVERLAY',font or 'GameFontNormal')
 t:SetPoint('TOPLEFT',parent,'TOPLEFT',x,-y);t:SetJustifyH('LEFT');t:SetText(value);return t
end
local function checkbox(parent,title,x,y,changed)
 local b=CreateFrame('CheckButton',nil,parent,'UICheckButtonTemplate')
 b:SetPoint('TOPLEFT',parent,'TOPLEFT',x,-y);b:SetSize(26,26)
 b.label=label(b,title,31,6,'GameFontHighlight')
 b:SetScript('OnClick',function(self)if not parent.refreshing then changed(self:GetChecked()==true)end end)
 return b
end
local function slider(parent,title,key,y,low,high,percent)
 local s=CreateFrame('Slider',nil,parent)
 s:SetPoint('TOPLEFT',parent,'TOPLEFT',30,-(y+23));s:SetSize(540,18)
 s:SetOrientation('HORIZONTAL');s:SetMinMaxValues(low,high);s:SetValueStep(1)
 if s.SetObeyStepOnDrag then s:SetObeyStepOnDrag(true)end
 local track=s:CreateTexture(nil,'BACKGROUND');track:SetColorTexture(.2,.25,.3,1)
 track:SetPoint('LEFT',s,'LEFT',0,0);track:SetPoint('RIGHT',s,'RIGHT',0,0);track:SetHeight(4)
 s:SetThumbTexture('Interface\\Buttons\\UI-SliderBar-Button-Horizontal')
 local thumb=s:GetThumbTexture();thumb:SetSize(28,28)
 label(parent,title,30,y)
 s.valueLabel=label(parent,'',475,y,'GameFontHighlight')
 s:SetScript('OnValueChanged',function(_,v)
  if parent.refreshing then return end
  local rounded=math.floor(v+.5)
  P:SetAppearance(key,percent and rounded/100 or rounded)
 end)
 return s
end
function P:RefreshOptions()
 local f=self.options;if not f or not self.db then return end
 f.refreshing=true
 f.auto:SetChecked(self.db.size==0);f.glow:SetChecked(self.db.castGlow)
 local custom=self.db.size>0 and self.db.size or self.db.customSize
 f.size:SetValue(custom);f.size.valueLabel:SetText(self.db.size==0 and 'Auto' or custom..' px')
 for _,key in ipairs({'offsetX','offsetY'})do
  f[key]:SetValue(self.db[key]);f[key].valueLabel:SetText(string.format('%+d px',self.db[key]))
 end
 for _,key in ipairs({'idleAlpha','cooldownAlpha'})do
  local percent=math.floor(self.db[key]*100+.5)
  f[key]:SetValue(percent);f[key].valueLabel:SetText(percent..'% opacity')
 end
 local size=self.db.size>0 and self.db.size or 32
 local row=self.rows[1];local icon=row and row.icon or 'Interface\\Icons\\Ability_Kick'
 for i,b in ipairs(f.previews)do
  b:SetSize(size,size);b.icon:SetTexture(icon);b.glow:SetSize(size*1.7,size*1.7)
  local alpha=i==1 and 1 or i==2 and self.db.idleAlpha or self.db.cooldownAlpha
  self:Paint(b,alpha,false,i==3 and '8'or '',i==1,i==1 and self.db.castGlow and 1 or 0)
 end
 f.notice:SetText(combat()and 'Opacity and glow apply now. Size and position apply after combat.'or 'Saved account-wide. Size and position apply on the next update.')
 f.refreshing=false
end
function P:OpenOptions()
 if not self.initialized then return end
 if self.spellOptions then self.spellOptions:Hide()end
 if self.options then self:RefreshOptions();self.options:Show();return end
 local f=CreateFrame('Frame','CounterCastOptions',UIParent)
 self.options=f;f:SetSize(600,670);f:SetPoint('CENTER',UIParent,'CENTER');f:SetFrameStrata('DIALOG')
 local sw,sh=UIParent:GetWidth(),UIParent:GetHeight()
 if sw and sh and sw>0 and sh>0 then f:SetScale(math.min(1,(sw-24)/600,(sh-24)/670))end
 local bg=f:CreateTexture(nil,'BACKGROUND');bg:SetAllPoints();bg:SetColorTexture(.055,.075,.10,.98)
 f:EnableMouse(true);f:SetMovable(true);f:SetClampedToScreen(true);f:RegisterForDrag('LeftButton')
 f:SetScript('OnDragStart',function(self)self:StartMoving()end)
 f:SetScript('OnDragStop',function(self)self:StopMovingOrSizing()end)
 f:SetScript('OnHide',function(self)self:StopMovingOrSizing()end)
 local close=CreateFrame('Button',nil,f,'UIPanelCloseButton');close:SetPoint('TOPRIGHT',f,'TOPRIGHT',-5,-5)
 close:SetScript('OnClick',function()f:Hide()end);f.close=close
 UISpecialFrames=UISpecialFrames or {};table.insert(UISpecialFrames,'CounterCastOptions')
 label(f,'CounterCast | Appearance',30,25,'GameFontNormalLarge')
 label(f,'Adjust your nameplate buttons. Changes save automatically.',30,55,'GameFontHighlightSmall')
 f.auto=checkbox(f,'Match health-bar thickness',26,82,function(checked)P:SetAppearance('size',checked and 0 or P.db.customSize)end)
 f.glow=checkbox(f,'Glow when enemy is casting',310,82,function(checked)P:SetAppearance('castGlow',checked)end)
 f.size=slider(f,'Button size (drag to use a custom size)','size',122,16,64)
 f.offsetX=slider(f,'Horizontal offset: left (-) / right (+)','offsetX',184,-100,100)
 f.offsetY=slider(f,'Vertical offset: down (-) / up (+)','offsetY',246,-80,80)
 f.idleAlpha=slider(f,'Opacity when nothing is casting','idleAlpha',308,0,100,true)
 f.cooldownAlpha=slider(f,'Opacity while the ability is on cooldown','cooldownAlpha',370,0,100,true)
 label(f,'0% = invisible   |   100% = solid   |   Both active: the fainter setting wins.',30,422,'GameFontHighlightSmall')
 label(f,'Preview: size and opacity (auto shown at 32 px)',30,452,'GameFontNormalSmall')
 f.previews={}
 for i,title in ipairs({'Casting / ready','Not casting','Cooldown'})do
  local x=30+(i-1)*185
  local bgbar=f:CreateTexture(nil,'BACKGROUND');bgbar:SetColorTexture(.55,.10,.13,1)
  bgbar:SetPoint('TOPLEFT',f,'TOPLEFT',x,-488);bgbar:SetSize(160,32)
  local b=CreateFrame('Frame',nil,f);b:SetPoint('RIGHT',bgbar,'RIGHT',-2,0)
  b.icon=b:CreateTexture(nil,'ARTWORK');b.icon:SetAllPoints()
  b.glow=b:CreateTexture(nil,'OVERLAY');b.glow:SetTexture('Interface\\Buttons\\UI-ActionButton-Border');b.glow:SetBlendMode('ADD');b.glow:SetPoint('CENTER',b,'CENTER')
  b.count=b:CreateFontString(nil,'OVERLAY','GameFontNormalSmall');b.count:SetPoint('CENTER',b,'CENTER')
  b.ready=b:CreateFontString(nil,'OVERLAY','GameFontNormalSmall');b.ready:SetPoint('BOTTOM',b,'TOP',0,1)
  f.previews[i]=b;label(f,title,x,542,'GameFontHighlightSmall')
 end
 f.notice=label(f,'',30,572,'GameFontHighlightSmall')
 label(f,'Large offsets may leave the nameplate mouseover area.',30,592,'GameFontHighlightSmall')
 label(f,'At 0%, the click area remains active during combat.',30,608,'GameFontHighlightSmall')
 local reset=CreateFrame('Button',nil,f,'UIPanelButtonTemplate');reset:SetSize(160,24);reset:SetPoint('BOTTOMLEFT',f,'BOTTOMLEFT',30,16);reset:SetText('Reset appearance')
 reset:SetScript('OnClick',function()P:ResetAppearance()end);f.reset=reset
 local spells=CreateFrame('Button',nil,f,'UIPanelButtonTemplate');spells:SetSize(160,24);spells:SetPoint('BOTTOMLEFT',f,'BOTTOMLEFT',210,16);spells:SetText('Choose spells')
 spells:SetScript('OnClick',function()P:OpenSpellOptions()end);f.spells=spells
 local done=CreateFrame('Button',nil,f,'UIPanelButtonTemplate');done:SetSize(100,24);done:SetPoint('BOTTOMRIGHT',f,'BOTTOMRIGHT',-30,16);done:SetText('Done');done:SetScript('OnClick',function()f:Hide()end)
 f:SetScript('OnShow',function()P:RefreshOptions()end)
 local elapsed=0;f:SetScript('OnUpdate',function(_,dt)elapsed=elapsed+dt;if elapsed>.3 then elapsed=0;P:RefreshOptions()end end)
 self:RefreshOptions();f:Show()
end

function P:SetSpellSelected(family,enabled)
 if not self.db then return end
 local _,class=UnitClass('player');local valid=false
 for _,row in ipairs(self:SpellChoices(class))do if row.family==family then valid=true;break end end
 if not valid then return end
 self.db.disabledSpells[tostring(family)]=not enabled and true or nil
 self.dirty=true
 if combat()then self.pending=true else self:Rebuild()end
 self:RefreshSpellOptions()
end
function P:SelectClassSpells(enabled)
 local _,class=UnitClass('player')
 for _,row in ipairs(self:SpellChoices(class))do self.db.disabledSpells[tostring(row.family)]=not enabled and true or nil end
 self.dirty=true
 if combat()then self.pending=true else self:Rebuild()end
 self:RefreshSpellOptions()
end
function P:RefreshSpellOptions()
 local f=self.spellOptions;if not f or not self.db then return end
 f.refreshing=true
 local className,class=UnitClass('player');local choices=self:SpellChoices(class);local selected=0
 f.subtitle:SetText((className or class)..' abilities. Choices save account-wide and follow all ranks.')
 f.controls:SetChecked(self.db.controls)
 for i,b in ipairs(f.rows)do
  local row=choices[i]
  if row then
   b.family=row.family;b:SetChecked(row.selected);b.label:SetText(row.name);b.icon:SetTexture(row.icon or 134400)
   local included=self.db.controls or row.kind:lower():find('interrupt',1,true)
   local state=not row.known and (row.pet and 'Requires the appropriate pet' or row.racial and 'Requires the matching racial ability' or 'Not learned yet') or not included and 'Blocked by the controls option above' or row.selected and 'Shown when available' or 'Not selected'
   b.detail:SetText(row.kind..'  |  '..state);b:Show()
   if row.known and row.selected and included then selected=selected+1 end
  else b:Hide()end
 end
 local message=selected==0 and 'No learned abilities selected: no buttons will be shown.' or selected..' learned abilities selected.'
 if combat()and (self.pending or self.dirty)then message=message..' Changes apply after combat.'end
 f.notice:SetText(message)
 f.refreshing=false
end
function P:OpenSpellOptions()
 if not self.initialized then return end
 if self.options then self.options:Hide()end
 if self.spellOptions then self:RefreshSpellOptions();self.spellOptions:Show();return end
 local f=CreateFrame('Frame','CounterCastSpellOptions',UIParent);self.spellOptions=f
 f:SetSize(600,500);f:SetPoint('CENTER',UIParent,'CENTER');f:SetFrameStrata('DIALOG')
 local sw,sh=UIParent:GetWidth(),UIParent:GetHeight()
 if sw and sh and sw>0 and sh>0 then f:SetScale(math.min(1,(sw-24)/600,(sh-24)/500))end
 local bg=f:CreateTexture(nil,'BACKGROUND');bg:SetAllPoints();bg:SetColorTexture(.055,.075,.10,.98)
 f:EnableMouse(true);f:SetMovable(true);f:SetClampedToScreen(true);f:RegisterForDrag('LeftButton')
 f:SetScript('OnDragStart',function(self)self:StartMoving()end);f:SetScript('OnDragStop',function(self)self:StopMovingOrSizing()end)
 f:SetScript('OnHide',function(self)self:StopMovingOrSizing()end)
 local close=CreateFrame('Button',nil,f,'UIPanelCloseButton');close:SetPoint('TOPRIGHT',f,'TOPRIGHT',-5,-5);close:SetScript('OnClick',function()f:Hide()end);f.close=close
 UISpecialFrames=UISpecialFrames or {};table.insert(UISpecialFrames,'CounterCastSpellOptions')
 label(f,'CounterCast | Spells',30,25,'GameFontNormalLarge')
 f.subtitle=label(f,'',30,55,'GameFontHighlightSmall');f.subtitle:SetSize(540,25)
 f.controls=checkbox(f,'Include stuns, fears, and other controls',26,82,function(checked)P:Setting('controls',checked);P:RefreshSpellOptions()end)
 f.rows={}
 local _,class=UnitClass('player')
 local count=0;for _,families in pairs(self.abilities)do count=math.max(count,#families+1)end
 for i=1,count do
  local y=132+(i-1)*56;local b
  b=checkbox(f,'',26,y,function(checked)P:SetSpellSelected(b.family,checked)end)
  b.label:ClearAllPoints();b.label:SetPoint('TOPLEFT',b,'TOPLEFT',65,-5);b.label:SetSize(475,20)
  b.icon=b:CreateTexture(nil,'ARTWORK');b.icon:SetSize(26,26);b.icon:SetPoint('LEFT',b,'RIGHT',5,0)
  b.detail=label(b,'',65,27,'GameFontHighlightSmall');b.detail:SetSize(475,20)
  f.rows[i]=b
 end
 f.notice=label(f,'',30,375,'GameFontHighlightSmall');f.notice:SetSize(540,34)
 label(f,'Unlearned spells stay unavailable until your character learns them.',30,417,'GameFontHighlightSmall')
 local function button(title,x,width,fn)
  local b=CreateFrame('Button',nil,f,'UIPanelButtonTemplate');b:SetSize(width,26);b:SetPoint('BOTTOMLEFT',f,'BOTTOMLEFT',x,20);b:SetText(title);b:SetScript('OnClick',fn);return b
 end
 f.all=button('Select all',30,140,function()P:SelectClassSpells(true)end)
 f.none=button('Select none',185,140,function()P:SelectClassSpells(false)end)
 f.done=button('Appearance',430,140,function()P:OpenOptions()end)
 f:SetScript('OnShow',function()P:RefreshSpellOptions()end)
 local elapsed=0;f:SetScript('OnUpdate',function(_,dt)elapsed=elapsed+dt;if elapsed>.3 then elapsed=0;P:RefreshSpellOptions()end end)
 self:RefreshSpellOptions();f:Show()
end

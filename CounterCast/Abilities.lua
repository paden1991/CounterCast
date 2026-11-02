local _,P=...
-- Candidate spell families only. Never grants an ability: the client must confirm
-- a learned rank. Controls are labeled separately and may fail on immune enemies.
P.abilities={
 WARRIOR={{kind='Interrupt',ids={6554,6552}},{kind='Interrupt',ids={1672,1671,72}},{kind='Stun',ids={12809}}},
 ROGUE={{kind='Interrupt',ids={1769,1768,1767,1766}},{kind='Stun',ids={8643,408}},{kind='Incapacitate',ids={11286,11285,8629,1777,1776}}},
 MAGE={{kind='Interrupt',ids={2139}}},
 SHAMAN={{kind='Interrupt',ids={10414,10413,10412,8046,8045,8044,8042}}},
 DRUID={{kind='Interrupt / charge',ids={16979}},{kind='Stun',ids={8983,6798,5211}}},
 HUNTER={{kind='Incapacitate',ids={19503}},{kind='Pet stun',ids={19577}}},
 PALADIN={{kind='Stun',ids={10308,5589,5588,853}}},
 PRIEST={{kind='Silence',ids={15487}},{kind='Fear',ids={10890,10888,8124,8122}}},
 WARLOCK={{kind='Pet interrupt',pet=true,ids={19647,19244}},{kind='Horror',ids={17926,17925,6789}}},
}
P.racial={kind='Stun',ids={20549}}
function P:IsPlain(v)
 if issecretvalue and issecretvalue(v) then return false end
 return true
end
function P:Known(id,pet)
 local ok,v
 if IsSpellKnown then ok,v=pcall(IsSpellKnown,id,pet==true)
 elseif C_SpellBook and C_SpellBook.IsSpellKnown then
  local bank=Enum and Enum.SpellBookSpellBank
  if pet and not bank then return false end
  ok,v=pcall(C_SpellBook.IsSpellKnown,id,bank and (pet and bank.Pet or bank.Player))
 elseif not pet and IsPlayerSpell then ok,v=pcall(IsPlayerSpell,id)end
 return ok and self:IsPlain(v) and v==true
end
function P:Spell(id)
 if C_Spell and C_Spell.GetSpellInfo then
  local ok,info=pcall(C_Spell.GetSpellInfo,id)
  if ok and info and self:IsPlain(info.name)then return info.name,info.iconID end
 elseif GetSpellInfo then
  local ok,name,_,icon=pcall(GetSpellInfo,id)
  if ok and self:IsPlain(name)then return name,icon end
 end
end
function P:Candidates(class)
 local out={};local families={}
 for _,row in ipairs(self.abilities[class]or {})do families[#families+1]=row end
 families[#families+1]=self.racial
 for _,row in ipairs(families)do
  for _,id in ipairs(row.ids)do if self:Known(id,row.pet)then
   local name,icon=self:Spell(id)
   if name then out[#out+1]={id=id,name=name,icon=icon,kind=row.kind,pet=row.pet}end
   break
  end end
 end
 return out
end
-- Return remaining seconds separately from cooldown activity. In combat the
-- client can expose activity while keeping the timing values secret.
function P:Cooldown(id)
 local start,duration,enabled,onGCD,active
 local function plainNumber(v)
  return self:IsPlain(v)and type(v)=='number'and v==v and math.abs(v)~=math.huge
 end
 local function plainBool(v)
  if self:IsPlain(v)and type(v)=='boolean'then return v end
 end
 if C_Spell and type(C_Spell.GetSpellCooldown)=='function'then
  local ok,info=pcall(C_Spell.GetSpellCooldown,id)
  if ok and self:IsPlain(info)and type(info)=='table'then
   start,duration,enabled,onGCD=info.startTime,info.duration,info.isEnabled,info.isOnGCD
   active=plainBool(info.isActive)
  end
 elseif type(GetSpellCooldown)=='function'then
  local ok;ok,start,duration,enabled=pcall(GetSpellCooldown,id)
  if not ok then start,duration,enabled=nil,nil,nil end
 end
 local remaining
 if self:IsPlain(enabled)and enabled~=false and enabled~=0 and plainNumber(start)and plainNumber(duration)then
  remaining=math.max(0,start+duration-GetTime())
  if plainBool(onGCD)==true then remaining=0 end
 end
 -- Prefer the native duration's activity with the global cooldown excluded.
 -- Never compare or perform arithmetic on a secret return value.
 local nativeActive
 if C_Spell and type(C_Spell.GetSpellCooldownDuration)=='function'then
  local ok,obj=pcall(C_Spell.GetSpellCooldownDuration,id,true)
  if ok and self:IsPlain(obj)and obj~=nil then
   local read,state=pcall(function()
    if type(obj.IsActive)=='function'then
     local value=obj:IsActive();local known=plainBool(value)
     if known~=nil then return known end
    end
    if type(obj.IsZero)=='function'then
     local value=obj:IsZero();local known=plainBool(value)
     if known~=nil then return not known end
    end
   end)
   if read then nativeActive=plainBool(state)end
  end
 end
 local source
 if nativeActive~=nil then
  active=nativeActive;source='native duration'
  if not active then remaining=0 elseif remaining==0 then remaining=nil end
 elseif remaining~=nil then active=remaining>0;source='readable timer'
 elseif active~=nil then source='activity flag'
 else source='unavailable'end
 if active==false then remaining=0 end
 self.cooldownStatus=self.cooldownStatus or {}
 self.cooldownStatus[id]={active=active,source=source}
 return remaining,active
end

-- Only a definite false means out of range; invalid/secret data stays unknown.
function P:Range(row,unit)
 local function read(u)
  local ok,value
  if C_Spell and type(C_Spell.IsSpellInRange)=='function'then
   ok,value=pcall(C_Spell.IsSpellInRange,row.id,u)
  elseif type(IsSpellInRange)=='function'then
   ok,value=pcall(IsSpellInRange,row.name,u)
  end
  if not ok or not self:IsPlain(value)then return nil end
  if value==true or value==1 then return true end
  if value==false or value==0 then return false end
 end
 local result=read(unit)
 if result~=nil then return result end
 -- Some client APIs reject nameplate tokens; aliases must match this enemy.
 for _,alias in ipairs({'mouseover','target'})do
  if type(UnitIsUnit)=='function'then
   local ok,same=pcall(UnitIsUnit,alias,unit)
   if ok and self:IsPlain(same)and same==true then
    result=read(alias);if result~=nil then return result end
   end
  end
 end
end

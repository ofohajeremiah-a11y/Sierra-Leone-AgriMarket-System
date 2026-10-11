from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta, date
import random
from api.models import *
class Command(BaseCommand):
 def handle(self,*args,**kwargs):
  User=get_user_model(); admin,_=User.objects.get_or_create(username='admin',defaults={'role':'admin','is_staff':True,'is_superuser':True,'phone_number':'+232000000'}); admin.role='admin';admin.is_staff=True;admin.is_superuser=True;admin.language='en';admin.set_password('admin123');admin.save()
  markets=[('Freetown','Western Area','Western'),('Bo','Bo','Southern'),('Makeni','Bombali','Northern'),('Kenema','Kenema','Eastern'),('Port Loko','Port Loko','North West')]
  for name,district,region in markets: Market.objects.get_or_create(name=name,defaults={'district':district,'region':region,'supply_capacity':1200 if name!='Freetown' else 700,'demand_baseline':1100 if name=='Freetown' else 650})
  commodities=[('Rice','kg',True),('Cassava','kg',False),('Maize','kg',True),('Groundnuts','kg',True),('Palm Oil','litre',True)]
  for name,unit,stor in commodities: Commodity.objects.get_or_create(name=name,defaults={'unit':unit,'storable':stor})
  random.seed(42); now=timezone.now()
  bases={'Rice':32,'Cassava':18,'Maize':24,'Groundnuts':38,'Palm Oil':45}; offsets={'Freetown':7,'Bo':0,'Makeni':-2,'Kenema':3,'Port Loko':1}
  for c in Commodity.objects.all():
   for m in Market.objects.all():
    for i in range(180):
     d=now-timedelta(days=179-i); seasonal=2.2*__import__('math').sin(i/12); val=bases[c.name]+offsets[m.name]+i*.035+seasonal+random.uniform(-1.5,1.5)
     PriceRecord.objects.get_or_create(market=m,commodity=c,recorded_at=d.replace(hour=10,minute=0,second=0,microsecond=0),defaults={'price':round(max(1,val),2),'volume':random.randint(100,900),'source':'demo','validated':True})
  for i in range(180):
   d=(now-timedelta(days=179-i)).date(); MacroIndicator.objects.get_or_create(date=d,defaults={'exchange_rate_sle_usd':22000+i*8,'cpi':100+i*.08,'inflation_pct':12+i*.01,'fuel_price_sle_litre':25+i*.01,'source':'demo'})
  for m in Market.objects.all():
   for i in range(180):
    d=(now-timedelta(days=179-i)).date(); ClimateRecord.objects.get_or_create(market=m,date=d,defaults={'rainfall_mm':max(0,random.gauss(7,10)),'temperature_c':27+random.uniform(-2,2),'source':'demo'})
   for c in Commodity.objects.all():
    SupplyDemandRecord.objects.get_or_create(market=m,commodity=c,date=now.date(),defaults={'supply_qty':m.supply_capacity*random.uniform(.6,1),'demand_qty':m.demand_baseline*random.uniform(.7,1.15),'source':'demo'})
  ms=list(Market.objects.all())
  for a in ms:
   for b in ms:
    if a.id!=b.id:
     dist=abs((a.id-b.id))*70+60
     TransportRoute.objects.get_or_create(origin=a,destination=b,defaults={'distance_km':dist,'base_cost_per_km':.8,'fuel_litre_per_km':.12,'spoilage_pct':2.0,'blocked':False})
  self.stdout.write(self.style.SUCCESS('Enhanced demo data loaded. Login: admin / admin123'))

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import random
from api.models import Market,Commodity,PriceRecord
class Command(BaseCommand):
    def handle(self,*args,**kwargs):
        User=get_user_model()
        admin,_=User.objects.get_or_create(username='admin',defaults={'role':'admin','is_staff':True,'is_superuser':True,'phone_number':'+232000000'})
        admin.role='admin'; admin.is_staff=True; admin.is_superuser=True; admin.set_password('admin123'); admin.save()
        for name,district in [('Freetown','Western Area'),('Bo','Bo'),('Makeni','Bombali')]: Market.objects.get_or_create(name=name,defaults={'district':district})
        for name,unit,stor in [('Rice','kg',True),('Cassava','kg',False),('Groundnuts','kg',True)]: Commodity.objects.get_or_create(name=name,defaults={'unit':unit,'storable':stor})
        random.seed(42); now=timezone.now()
        for c in Commodity.objects.all():
            base={'Rice':32,'Cassava':18,'Groundnuts':38}[c.name]
            for m in Market.objects.all():
                offset={'Freetown':7,'Bo':0,'Makeni':-2}[m.name]
                for i in range(28):
                    d=now-timedelta(days=27-i); val=base+offset+(i*0.12)+random.uniform(-1.8,1.8)
                    PriceRecord.objects.get_or_create(market=m,commodity=c,recorded_at=d.replace(hour=10,minute=0,second=0,microsecond=0),defaults={'price':round(max(1,val),2),'volume':random.randint(50,500),'source':'demo','validated':True})
        self.stdout.write(self.style.SUCCESS('Demo data loaded. Login: admin / admin123'))

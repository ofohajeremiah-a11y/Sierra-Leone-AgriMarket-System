from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [('auth','0012_alter_user_first_name_max_length')]
    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(auto_now_add=False, verbose_name='date joined')),
                ('role', models.CharField(choices=[('farmer','Farmer'),('trader','Trader'),('enumerator','Enumerator'),('policymaker','Policymaker'),('admin','Administrator')], default='farmer', max_length=20)),
                ('phone_number', models.CharField(blank=True, max_length=30, null=True, unique=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={'abstract': False},
        ),
        migrations.CreateModel(name='Market', fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('name',models.CharField(max_length=100,unique=True)),('district',models.CharField(max_length=100)),('latitude',models.DecimalField(blank=True,decimal_places=6,max_digits=9,null=True)),('longitude',models.DecimalField(blank=True,decimal_places=6,max_digits=9,null=True)),('active',models.BooleanField(default=True))]),
        migrations.CreateModel(name='Commodity', fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('name',models.CharField(max_length=100,unique=True)),('unit',models.CharField(default='kg',max_length=30)),('storable',models.BooleanField(default=True)),('active',models.BooleanField(default=True))]),
        migrations.CreateModel(name='PriceRecord', fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('price',models.DecimalField(decimal_places=2,max_digits=12)),('volume',models.DecimalField(decimal_places=2,default=0,max_digits=12)),('recorded_at',models.DateTimeField()),('source',models.CharField(default='manual',max_length=100)),('validated',models.BooleanField(default=False)),('created_at',models.DateTimeField(auto_now_add=True)),('commodity',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='prices',to='api.commodity')),('market',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='prices',to='api.market')),('submitted_by',models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,to='api.user'))], options={'ordering':['-recorded_at']},),
        migrations.CreateModel(name='Forecast', fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('forecast_date',models.DateField()),('predicted_price',models.DecimalField(decimal_places=2,max_digits=12)),('lower_bound',models.DecimalField(decimal_places=2,max_digits=12)),('upper_bound',models.DecimalField(decimal_places=2,max_digits=12)),('model_name',models.CharField(default='ARIMA',max_length=50)),('rmse',models.DecimalField(blank=True,decimal_places=4,max_digits=12,null=True)),('created_at',models.DateTimeField(auto_now_add=True)),('commodity',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,to='api.commodity')),('market',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,to='api.market'))], options={'ordering':['forecast_date']}),
        migrations.CreateModel(name='Recommendation', fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('quantity',models.DecimalField(decimal_places=2,max_digits=12)),('action',models.CharField(default='transport',max_length=30)),('expected_margin',models.DecimalField(decimal_places=2,max_digits=12)),('confidence',models.DecimalField(decimal_places=2,max_digits=5)),('rationale',models.TextField()),('created_at',models.DateTimeField(auto_now_add=True)),('commodity',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,to='api.commodity')),('destination',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='recommendation_destinations',to='api.market')),('origin',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='recommendation_origins',to='api.market'))]),
        migrations.CreateModel(name='Alert', fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('message',models.CharField(max_length=255)),('sent',models.BooleanField(default=False)),('created_at',models.DateTimeField(auto_now_add=True)),('commodity',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,to='api.commodity')),('market',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,to='api.market')),('user',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='alerts',to='api.user'))]),
        migrations.AddIndex(model_name='pricerecord', index=models.Index(fields=['market','commodity','recorded_at'], name='api_pricere_market_i_9bb7b0_idx')),
    ]

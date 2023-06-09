# Generated by Django 4.0.3 on 2022-03-01 12:14

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='NFVO',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('osm', 'osm'), ('sonata', 'sonata')], max_length=6)),
                ('name', models.CharField(max_length=50)),
                ('authKey', models.BinaryField(max_length=16, validators=[django.core.validators.MinLengthValidator(16)])),
                ('nfvo_ip', models.GenericIPAddressField()),
                ('nfvo_id_at_slicem', models.CharField(max_length=100)),
                ('nfvo_id2_at_slicem', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='RelationSliceM2VIM',
            fields=[
                ('vim_id_at_slicem', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('vim_id2_at_slicem', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Resource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('resource_id_at_slicem', models.CharField(max_length=100)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Resource_state',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime', models.DateTimeField()),
                ('state', models.CharField(choices=[('ordinary', 'ordinary'), ('suspicious', 'suspicious'), ('attack', 'attack')], max_length=10)),
                ('resource', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='mtdcontroller.resource')),
            ],
        ),
        migrations.CreateModel(
            name='VIM',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('environment', models.CharField(choices=[('Openstack', 'Openstack'), ('OpenVIM', 'OpenVIM'), ('Azure', 'Azure'), ('VMware', 'VMware')], max_length=9)),
                ('location', models.CharField(max_length=100)),
                ('cores', models.IntegerField(validators=[django.core.validators.MinValueValidator(2)])),
                ('memory_mb', models.IntegerField(validators=[django.core.validators.MinValueValidator(2048)])),
                ('disk_gb', models.IntegerField(validators=[django.core.validators.MinValueValidator(20)])),
                ('vim_ip', models.GenericIPAddressField()),
                ('vim_port', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10000)])),
                ('vim_url', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='NS',
            fields=[
                ('resource_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='mtdcontroller.resource')),
                ('primary_ip', models.GenericIPAddressField()),
                ('resource_id_at_nfvo', models.CharField(max_length=100)),
                ('is_running', models.BooleanField()),
            ],
            options={
                'abstract': False,
            },
            bases=('mtdcontroller.resource',),
        ),
        migrations.CreateModel(
            name='NS_state',
            fields=[
                ('resource_state_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='mtdcontroller.resource_state')),
                ('is_running', models.BooleanField()),
                ('current_nss_list', models.ManyToManyField(to='mtdcontroller.ns_state')),
            ],
            bases=('mtdcontroller.resource_state',),
        ),
        migrations.CreateModel(
            name='VIM_state',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime', models.DateTimeField()),
                ('remaining_cores', models.IntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('remaining_memory_mb', models.IntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('remaining_disk_gb', models.IntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('state', models.CharField(choices=[('ordinary', 'ordinary'), ('suspicious', 'suspicious'), ('attack', 'attack')], max_length=10)),
                ('vim', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='mtdcontroller.vim')),
            ],
        ),
        migrations.CreateModel(
            name='SliceM',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('authKey', models.BinaryField(max_length=16, validators=[django.core.validators.MinLengthValidator(16)])),
                ('slicem_ip', models.GenericIPAddressField()),
                ('slicem_port', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(65355)])),
                ('type', models.CharField(choices=[('katana', 'katana'), ('osm', 'osm')], max_length=6)),
                ('vims', models.ManyToManyField(through='mtdcontroller.RelationSliceM2VIM', to='mtdcontroller.vim')),
            ],
        ),
        migrations.AddField(
            model_name='resource_state',
            name='vim_hosts',
            field=models.ManyToManyField(to='mtdcontroller.vim_state'),
        ),
        migrations.AddField(
            model_name='resource',
            name='slicem',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mtdcontroller.slicem'),
        ),
        migrations.AddField(
            model_name='relationslicem2vim',
            name='slicem',
            field=models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='mtdcontroller.slicem'),
        ),
        migrations.AddField(
            model_name='relationslicem2vim',
            name='vim',
            field=models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='mtdcontroller.vim'),
        ),
        migrations.CreateModel(
            name='RelationNFVO2VIM',
            fields=[
                ('vim_id_at_nfvo', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('nfvo', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='mtdcontroller.nfvo')),
                ('vim', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='mtdcontroller.vim')),
            ],
        ),
        migrations.AddField(
            model_name='nfvo',
            name='slicem',
            field=models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='mtdcontroller.slicem'),
        ),
        migrations.AddField(
            model_name='nfvo',
            name='vims_list',
            field=models.ManyToManyField(through='mtdcontroller.RelationNFVO2VIM', to='mtdcontroller.vim'),
        ),
        migrations.CreateModel(
            name='VNF_state',
            fields=[
                ('resource_state_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='mtdcontroller.resource_state')),
                ('cores', models.IntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('memory_mb', models.IntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('disk_gb', models.IntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('ns_parent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mtdcontroller.ns_state')),
            ],
            bases=('mtdcontroller.resource_state',),
        ),
        migrations.CreateModel(
            name='VNF',
            fields=[
                ('resource_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='mtdcontroller.resource')),
                ('resource_id_at_nfvo', models.CharField(max_length=100)),
                ('real_ipv4', models.GenericIPAddressField(null=True, protocol='ipv4')),
                ('real_ipv6', models.GenericIPAddressField(null=True, protocol='ipv6')),
                ('req_cores', models.IntegerField()),
                ('req_memory_mb', models.IntegerField()),
                ('req_disk_gb', models.IntegerField()),
                ('nfvo', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='mtdcontroller.nfvo')),
                ('ns_parent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mtdcontroller.ns')),
                ('vim', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mtdcontroller.vim')),
            ],
            options={
                'db_table': 'vnf_table',
                'abstract': False,
            },
            bases=('mtdcontroller.resource',),
        ),
        migrations.CreateModel(
            name='VDU_state',
            fields=[
                ('resource_state_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='mtdcontroller.resource_state')),
                ('req_cores', models.IntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('req_memory_mb', models.IntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('req_disk_gb', models.IntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('is_running', models.BooleanField()),
                ('vnf_parent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mtdcontroller.vnf_state')),
            ],
            bases=('mtdcontroller.resource_state',),
        ),
        migrations.CreateModel(
            name='VDU',
            fields=[
                ('resource_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='mtdcontroller.resource')),
                ('id_at_nfvo', models.CharField(max_length=100)),
                ('image_name', models.CharField(max_length=100)),
                ('real_ipv4', models.GenericIPAddressField(null=True, protocol='ipv4')),
                ('real_ipv6', models.GenericIPAddressField(null=True, protocol='ipv6')),
                ('req_cores', models.IntegerField()),
                ('req_memory_mb', models.IntegerField()),
                ('req_disk_gb', models.IntegerField()),
                ('is_running', models.BooleanField()),
                ('vnf_parent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mtdcontroller.vnf')),
            ],
            options={
                'abstract': False,
            },
            bases=('mtdcontroller.resource',),
        ),
        migrations.CreateModel(
            name='NSi_state',
            fields=[
                ('resource_state_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='mtdcontroller.resource_state')),
                ('is_running', models.BooleanField()),
                ('current_ns_list', models.ManyToManyField(to='mtdcontroller.ns_state')),
            ],
            bases=('mtdcontroller.resource_state',),
        ),
        migrations.CreateModel(
            name='NSi',
            fields=[
                ('resource_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='mtdcontroller.resource')),
                ('is_running', models.BooleanField()),
                ('nfvos_list', models.ManyToManyField(to='mtdcontroller.nfvo')),
                ('nss_list', models.ManyToManyField(to='mtdcontroller.ns')),
            ],
            options={
                'abstract': False,
            },
            bases=('mtdcontroller.resource',),
        ),
        migrations.AddField(
            model_name='ns',
            name='nfvo',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mtdcontroller.nfvo'),
        ),
        migrations.AddField(
            model_name='ns',
            name='nss_list',
            field=models.ManyToManyField(to='mtdcontroller.ns'),
        ),
        migrations.CreateModel(
            name='Interface',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('external_conn_point', models.CharField(max_length=100)),
                ('mgmt_vnf', models.BooleanField()),
                ('ns_vld_id', models.CharField(max_length=100)),
                ('ip', models.GenericIPAddressField()),
                ('mac', models.CharField(max_length=100)),
                ('vdu', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mtdcontroller.vdu')),
            ],
        ),
    ]

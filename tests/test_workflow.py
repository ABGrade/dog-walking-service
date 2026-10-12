"""Integration checks against a separately initialized demo database."""
from pathlib import Path
from datetime import datetime, timedelta
import sys
import uuid
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
import database

def test_full_walk_workflow():
    token=uuid.uuid4().hex[:12]
    owner=database.register_user('Test Owner','+70000000000',f'owner-{token}@example.test','demo-password',False)
    walker=database.register_user('Test Walker','+70000000001',f'walker-{token}@example.test','demo-password',True)
    assert owner and walker
    assert database.add_dog(owner['id'],'Test Dog',1,'М','2020-01-01','','')
    dog=database.get_user_dogs(owner['id'])[0]
    start=datetime.now()+timedelta(days=1)
    assert database.create_order(owner['id'],dog['id'],start,start-timedelta(hours=1),'Test address','') is None
    order=database.create_order(owner['id'],dog['id'],start,start+timedelta(hours=1),'Test address','Test comment')
    assert order
    assert order in [row['id'] for row in database.get_available_orders()]
    assert database.accept_order(order,walker['id'])
    assert not database.accept_order(order,walker['id'])
    assert order not in [row['id'] for row in database.get_available_orders()]
    walk=database.start_walk(order)
    assert walk
    assert database.finish_walk(order,walk)
    assert database.update_report(walk,'Completed demo walk')
    detail=database.get_order_details_for_client(order)
    assert detail['status_id']==3
    assert detail['report_summary']=='Completed demo walk'

def test_foreign_dog_is_rejected():
    owner=database.authenticate_user('owner@example.test','dog_demo')
    walker=database.authenticate_user('walker@example.test','dog_demo')
    dog=database.get_user_dogs(owner['id'])[0]
    start=datetime.now()+timedelta(days=1)
    assert database.create_order(walker['id'],dog['id'],start,start+timedelta(hours=1),'Test','') is None

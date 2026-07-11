from .service_generator import GeneratorLogic
from api.models import ServiceInstance

try:
    from celery import shared_task
except ImportError:
    # Fallback for environments without Celery
    def shared_task(func):
        return func

@shared_task
def create_service_task(instance_id):
    try:
        instance = ServiceInstance.objects.get(id=instance_id)
        # In service_generator.py, GeneratorLogic constructor expects instance_id
        logic = GeneratorLogic(instance_id)
        
        logic.prepare_files()
        logic.generate_configs()
        logic.start_service()
        logic.update_proxy()
        
        # Successo!
        instance.status = ServiceInstance.ServiceStatus.RUNNING
        instance.save()
        
    except Exception as e:
        # Errore!
        instance = ServiceInstance.objects.get(id=instance_id) # Ricarica l'oggetto
        instance.status = ServiceInstance.ServiceStatus.ERROR
        instance.description = f"Creazione fallita: {str(e)}"
        instance.save()

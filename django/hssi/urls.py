from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
import website.admin

urlpatterns = [
    path('admin/', website.admin.site.urls),
    path('', include('website.urls'))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

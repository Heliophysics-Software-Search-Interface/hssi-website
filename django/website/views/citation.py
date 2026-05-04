import requests
from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.http import require_GET


ALLOWED_STYLES = {
    'apa',
    'harvard-cite-them-right',
    'modern-language-association',
    'vancouver',
    'chicago-fullnote-bibliography',
    'ieee',
    'bibtex',
    'nature',
    'science',
    'american-geophysical-union',
    'elsevier-harvard',
}

CACHE_TTL = 60 * 60  # 1 hour


@require_GET
def get_citation(request):
    doi = request.GET.get('doi', '')
    style = request.GET.get('style', 'apa')

    if not doi.startswith('https://doi.org/'):
        return JsonResponse({'error': 'Invalid DOI URL'}, status=400)

    if style not in ALLOWED_STYLES:
        return JsonResponse({'error': 'Unsupported citation style'}, status=400)

    cache_key = f'citation:{doi}:{style}'
    cached = cache.get(cache_key)
    if cached is not None:
        return JsonResponse({'citation': cached})

    try:
        response = requests.get(
            doi,
            headers={'Accept': f'text/x-bibliography; style={style}'},
            timeout=45,
        )
        response.raise_for_status()
        response.encoding = 'utf-8'
        citation = response.text.strip()
        cache.set(cache_key, citation, CACHE_TTL)
        return JsonResponse({'citation': citation})
    except requests.exceptions.Timeout:
        return JsonResponse({'error': 'DOI service timed out'}, status=504)
    except requests.exceptions.RequestException as e:
        return JsonResponse({'error': f'Failed to fetch citation: {e}'}, status=502)

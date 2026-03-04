import requests
from django.http import JsonResponse


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


def get_citation(request):
    doi = request.GET.get('doi', '')
    style = request.GET.get('style', 'apa')

    if not doi.startswith('https://doi.org/'):
        return JsonResponse({'error': 'Invalid DOI URL'}, status=400)

    if style not in ALLOWED_STYLES:
        return JsonResponse({'error': 'Unsupported citation style'}, status=400)

    try:
        response = requests.get(
            doi,
            headers={'Accept': f'text/x-bibliography; style={style}'},
            timeout=10,
        )
        response.raise_for_status()
        response.encoding = 'utf-8'
        citation = response.text.strip()
        return JsonResponse({'citation': citation})
    except requests.exceptions.Timeout:
        return JsonResponse({'error': 'DOI service timed out'}, status=504)
    except requests.exceptions.RequestException as e:
        return JsonResponse({'error': f'Failed to fetch citation: {e}'}, status=502)

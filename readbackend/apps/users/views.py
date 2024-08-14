
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .services import match_audio_to_text

@method_decorator(csrf_exempt, name='dispatch')
class AudioMatchView(View):
    def post(self, request):
        session_id = request.POST.get('session_id')
        audio_file = request.FILES.get('audio_file')

        if not session_id or not audio_file:
            return JsonResponse({'error': 'Invalid input'}, status=400)

        # try:
        #     session = ReadingSession.objects.get(id=session_id)
        # except ReadingSession.DoesNotExist:
        #     return JsonResponse({'error': 'Reading session not found'}, status=404)

        # story = session.story
        # start_word_index = int(session.progress * story.word_count)
        # matching_text = " ".join(story.content.split()[start_word_index:])
        matching_text = "the quick brown fox jumps over the lazy dog"
        match_result = match_audio_to_text(audio_file, matching_text)

        return JsonResponse({'match': match_result})

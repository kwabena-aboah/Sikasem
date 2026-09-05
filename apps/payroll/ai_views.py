"""
apps/payroll/ai_views.py
AI Advisor endpoints as a proper ViewSet with list() action.
"""
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .ai import ComplianceAdvisor, PayrollForecaster


class AIAdvisorViewSet(viewsets.ViewSet):
    """AI-powered payroll features"""
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        """Returns available AI features"""
        return Response({
            'features': [
                {'id': 'compliance', 'name': 'Compliance Advisor', 'description': 'Ask Ghana payroll compliance questions'},
                {'id': 'forecast',   'name': 'Payroll Forecast',   'description': 'Forecast future payroll costs'},
            ]
        })

    @action(detail=False, methods=['post'])
    def compliance_question(self, request):
        """Ask the AI compliance advisor a question"""
        question = request.data.get('question', '').strip()
        if not question:
            return Response({'error': 'Question is required'}, status=400)

        advisor = ComplianceAdvisor()
        company_context = {}
        if request.user.company:
            company_context = {
                'name': request.user.company.name,
                'employee_count': request.user.company.employees.filter(status='active').count(),
            }

        answer = advisor.ask(question, company_context)
        return Response({'question': question, 'answer': answer})

    @action(detail=False, methods=['get'])
    def forecast(self, request):
        """Get payroll cost forecast"""
        months = int(request.query_params.get('months', 3))
        months = max(1, min(months, 12))  # clamp 1–12

        if not request.user.company:
            return Response({'error': 'No company linked to your account'}, status=400)

        forecaster = PayrollForecaster()
        result = forecaster.forecast_next_months(request.user.company, months)
        return Response(result)

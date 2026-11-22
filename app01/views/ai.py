"""AI 智能助手：招聘 JD 生成、制度知识库问答、数据智能点评。

所有大模型调用统一走 LLMClient.chat()，并用 try/except 兜底，
保证接口失败时返回友好 JSON，而不是让页面崩溃。
"""
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render

from app01.middleware.auth import require_permission
from app01.models import Attendance, Employee, Knowledge, Salary
from app01.utils.ai import LLMClient, LLMError
from app01.utils.prompts import (
    DATA_SYSTEM,
    JD_SYSTEM,
    QA_SYSTEM,
    build_data_prompt,
    build_jd_prompt,
    build_qa_prompt,
)


def _safe_chat(prompt, system=None):
    """统一兜底：成功返回 (文本, None)，失败返回 (None, 错误信息)。"""
    try:
        return LLMClient.chat(prompt, system=system), None
    except LLMError as e:
        return None, str(e)


@require_permission('ai_assistant')
def assistant(request):
    """AI 助手主页：三块功能在同一页面，员工下拉数据传给模板。"""
    employees = Employee.objects.all().order_by('id')
    return render(request, 'ai.html', {'employees': employees})


@require_permission('ai_assistant')
def generate_jd(request):
    """模块 A：输入岗位名称，返回结构化招聘 JD。"""
    title = (request.POST.get('title') or '').strip()[:32]  # T6：限制长度
    if not title:
        return JsonResponse({'status': False, 'error': '岗位名称不能为空'})

    text, err = _safe_chat(build_jd_prompt(title), system=JD_SYSTEM)
    if err:
        return JsonResponse({'status': False, 'error': err})
    return JsonResponse({'status': True, 'data': text})


@require_permission('ai_assistant')
def knowledge_qa(request):
    """模块 B：制度知识库问答。

    流程：SQL 关键词检索相关制度 -> 拼入提示词 -> 模型照着资料回答；
    没检索到资料时直接回答"不知道"，不调用模型。
    """
    question = (request.POST.get('question') or '').strip()[:200]  # T6：限制长度
    if not question:
        return JsonResponse({'status': False, 'error': '问题不能为空'})

    # 切词：先按空格+中文标点拆，再对长片段做 2 字滑动窗口（中文无空格，
    # 二元分词是课程里最简、可讲清的检索方式）。
    import re
    raw_words = re.split(r'[\s，。？！、；：""''（）\.,\?!;:]+', question)
    keywords = set()
    for w in raw_words:
        if len(w) >= 2:
            keywords.add(w)
            # 2 字滑动窗口，覆盖"报销款几天到账"->报销/销款/款几...
            for i in range(len(w) - 1):
                keywords.add(w[i:i + 2])
    keywords = [w for w in keywords if len(w) >= 2] or [question]
    q = Q()
    for w in keywords:
        q |= Q(title__icontains=w) | Q(content__icontains=w)
    items = Knowledge.objects.filter(q)[:5]

    if not items:
        return JsonResponse({'status': True, 'data': '不知道，资料中暂无相关制度。'})

    context = '\n'.join(f'《{k.title}》\n{k.content}' for k in items)
    text, err = _safe_chat(build_qa_prompt(question, context), system=QA_SYSTEM)
    if err:
        return JsonResponse({'status': False, 'error': err})
    return JsonResponse({'status': True, 'data': text})


@require_permission('ai_assistant')
def data_comment(request):
    """模块 C：读取某员工某月薪资+考勤数据，生成一句客观点评。"""
    emp_id = request.POST.get('employee_id', '')
    month = (request.POST.get('month') or '').strip()[:7]  # 形如 2026-11

    emp = Employee.objects.filter(pk=emp_id).first()
    if not emp:
        return JsonResponse({'status': False, 'error': '请选择员工'})
    if not month:
        return JsonResponse({'status': False, 'error': '请填写月份（格式 YYYY-MM）'})

    # 1) 拼薪资文本
    parts = [f'员工：{emp.name}，{month}月']
    sal = Salary.objects.filter(employee=emp, month=month).first()
    if sal:
        parts.append(
            f'薪资：基本工资{sal.basic}元，奖金{sal.bonus}元，'
            f'扣款{sal.deduction}元，实发{sal.total}元'
        )
    else:
        parts.append('薪资：本月无薪资记录')

    # 2) 拼考勤统计文本
    atts = Attendance.objects.filter(employee=emp, date__startswith=month)
    parts.append(
        f'考勤：迟到{atts.filter(status=2).count()}次，'
        f'早退{atts.filter(status=3).count()}次，'
        f'缺勤{atts.filter(status=4).count()}次（共{atts.count()}条记录）'
    )

    data_text = '；'.join(parts)
    text, err = _safe_chat(build_data_prompt(data_text), system=DATA_SYSTEM)
    if err:
        return JsonResponse({'status': False, 'error': err})
    return JsonResponse({'status': True, 'data': text})

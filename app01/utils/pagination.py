"""通用分页组件。

在视图查询集上调用 Pagination(queryset, request, per_page)，
即可得到当前页数据、页数列表，以及适合渲染的分页 HTML。
"""
from django.utils.safestring import mark_safe


class Pagination:
    """对象列表分页。"""

    def __init__(self, queryset, request, per_page=10, page_param='page'):
        self.queryset = queryset
        self.request = request
        self.per_page = per_page
        self.page_param = page_param

        try:
            page = int(request.GET.get(page_param, '1'))
        except (TypeError, ValueError):
            page = 1
        self.current_page = max(page, 1)

        self.total_count = queryset.count()
        self.total_page = max((self.total_count + per_page - 1) // per_page, 1)
        if self.current_page > self.total_page:
            self.current_page = self.total_page

        self.start = (self.current_page - 1) * per_page
        self.end = self.start + per_page
        self.page_queryset = queryset[self.start:self.end]

    def page_html(self):
        """渲染分页按钮（保留除 page 外的查询参数）。"""
        if self.total_page <= 1:
            return ''

        # 保留当前查询串（去掉 page 参数），保证搜索/筛选时分页不丢失条件
        params = self.request.GET.copy()
        if self.page_param in params:
            params.pop(self.page_param)
        qs = '&'.join(f'{k}={v}' for k, v in params.items())
        prefix = ('?' + qs + '&') if qs else '?'
        url = f'{self.request.path}{prefix}{self.page_param}='

        # 最多显示 9 个页码
        half = 4
        start_page = max(1, self.current_page - half)
        end_page = min(self.total_page, self.current_page + half)

        html = ['<ul class="pagination pagination-sm" style="margin:0">']
        # 上一页
        if self.current_page > 1:
            html.append(f'<li><a href="{url}{self.current_page - 1}">&laquo;</a></li>')
        for i in range(start_page, end_page + 1):
            if i == self.current_page:
                html.append(f'<li class="active"><span>{i}</span></li>')
            else:
                html.append(f'<li><a href="{url}{i}">{i}</a></li>')
        # 下一页
        if self.current_page < self.total_page:
            html.append(f'<li><a href="{url}{self.current_page + 1}">&raquo;</a></li>')
        html.append('</ul>')
        return mark_safe(''.join(html))

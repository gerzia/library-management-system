// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 确认删除弹窗
    const deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            if (!confirm('确定要删除吗？此操作不可恢复！')) {
                e.preventDefault();
            }
        });
    });

    // 借阅确认弹窗
    const borrowButtons = document.querySelectorAll('.btn-borrow');
    borrowButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            const title = this.getAttribute('data-title');
            if (!confirm(`确定要借阅《${title}》吗？`)) {
                e.preventDefault();
            }
        });
    });

    // 归还确认弹窗
    const returnButtons = document.querySelectorAll('.btn-return');
    returnButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            const title = this.getAttribute('data-title');
            if (!confirm(`确定要归还《${title}》吗？`)) {
                e.preventDefault();
            }
        });
    });

    // 搜索框回车提交
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                document.getElementById('search-form').submit();
            }
        });
    }

    // 隐藏过期提示框
    const alertElements = document.querySelectorAll('.alert');
    alertElements.forEach(alert => {
        const closeBtn = alert.querySelector('.btn-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                alert.style.display = 'none';
            });
        }
        // 5秒后自动隐藏提示框
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => {
                alert.style.display = 'none';
            }, 500);
        }, 5000);
    });
});
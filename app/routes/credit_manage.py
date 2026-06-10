"""
挂账管理路由：挂账单位/记录、结款还款
"""
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.forms import CreditForm, CreditPaymentForm
from app.models import Credit, OrderRecord

cr_bp = Blueprint('credit', __name__)


@cr_bp.route('/')
@login_required
def credit_list():
    """挂账记录列表"""
    status = request.args.get('status', '').strip()
    company = request.args.get('company', '').strip()

    query = Credit.query
    if status:
        query = query.filter_by(pay_status=status)
    if company:
        query = query.filter(Credit.company_name.contains(company))

    credits = query.order_by(Credit.create_time.desc()).all()

    # 汇总统计
    stats = {
        'total_debt': db.session.query(db.func.sum(Credit.debt_fee)).scalar() or 0,
        'unpaid_count': Credit.query.filter(Credit.pay_status.in_(
            [Credit.PAY_UNPAID, Credit.PAY_PARTIAL])).count(),
        'total_unpaid': db.session.query(db.func.sum(Credit.debt_fee)).filter(
            Credit.pay_status.in_([Credit.PAY_UNPAID, Credit.PAY_PARTIAL])
        ).scalar() or 0,
    }

    # 所有未取消的已确认订单（可用于挂账）
    available_orders = OrderRecord.query.filter(
        OrderRecord.order_status == OrderRecord.ORDER_CONFIRMED
    ).order_by(OrderRecord.create_time.desc()).all()

    return render_template('credit/list.html', credits=credits,
                           stats=stats, available_orders=available_orders)


@cr_bp.route('/create', methods=['POST'])
@login_required
def credit_create():
    """新增挂账"""
    form = CreditForm()
    if form.validate_on_submit():
        # 检查该订单是否已有挂账
        existing = Credit.query.filter_by(order_id=form.order_id.data).first()
        if existing:
            flash(f'该订单已存在挂账记录（{existing.company_name}）', 'danger')
            return redirect(url_for('credit.credit_list'))

        credit = Credit(
            company_name=form.company_name.data,
            order_id=form.order_id.data,
            debt_fee=form.debt_fee.data
        )
        db.session.add(credit)
        db.session.commit()
        flash(f'挂账成功！{credit.company_name} · ¥{credit.debt_fee:.0f}', 'success')
    else:
        for errs in form.errors.values():
            for e in errs: flash(e, 'danger')
    return redirect(url_for('credit.credit_list'))


@cr_bp.route('/<int:credit_id>/pay', methods=['POST'])
@login_required
def credit_pay(credit_id):
    """挂账还款/结款"""
    credit = db.session.get(Credit, credit_id)
    if not credit:
        flash('挂账记录不存在', 'danger')
        return redirect(url_for('credit.credit_list'))
    if credit.pay_status == Credit.PAY_FULL:
        flash('该挂账已还清', 'info')
        return redirect(url_for('credit.credit_list'))

    form = CreditPaymentForm()
    if form.validate_on_submit():
        pay = form.pay_amount.data
        remaining = float(credit.remaining_debt)
        if float(pay) > remaining:
            flash(f'还款金额不能超过剩余欠款 ¥{remaining:.0f}', 'danger')
        else:
            credit.make_payment(pay)
            db.session.commit()
            flash(f'还款成功！¥{pay:.0f} · {credit.company_name} · '
                  f'剩余欠款 ¥{float(credit.remaining_debt):.0f}', 'success')
    else:
        for errs in form.errors.values():
            for e in errs: flash(e, 'danger')
    return redirect(url_for('credit.credit_list'))


@cr_bp.route('/<int:credit_id>/delete', methods=['POST'])
@login_required
def credit_delete(credit_id):
    """删除挂账记录"""
    credit = db.session.get(Credit, credit_id)
    if not credit:
        flash('挂账记录不存在', 'danger')
    elif credit.paid_amount and float(credit.paid_amount) > 0:
        flash('已有还款记录的挂账不可删除', 'danger')
    else:
        db.session.delete(credit)
        db.session.commit()
        flash('挂账记录已删除', 'success')
    return redirect(url_for('credit.credit_list'))

"""
客房评价路由
"""
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.models import Review, Room

rv_bp = Blueprint('review', __name__)


@rv_bp.route('/<int:room_id>')
@login_required
def room_reviews(room_id):
    """查看某房间的评价列表"""
    room = db.session.get(Room, room_id)
    if not room: flash('房间不存在', 'danger'); return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    pagination = room.reviews.order_by(Review.create_time.desc()).paginate(
        page=page, per_page=10, error_out=False)
    return render_template('review/list.html', room=room, pagination=pagination)


@rv_bp.route('/create', methods=['POST'])
@login_required
def create_review():
    """提交评价"""
    room_id = request.form.get('room_id', type=int)
    rating = request.form.get('rating', type=int)
    content = request.form.get('content', '').strip()
    tags = request.form.get('tags', '').strip()

    room = db.session.get(Room, room_id)
    if not room:
        flash('房间不存在', 'danger')
        return redirect(url_for('main.index'))
    if not rating or rating < 1 or rating > 5:
        flash('请选择1-5星评分', 'danger')
        return redirect(url_for('room.room_detail', room_id=room_id))

    review = Review(room_id=room_id, user_id=current_user.id,
                    rating=rating, content=content, tags=tags)
    db.session.add(review)
    db.session.commit()

    flash(f'评价提交成功！{rating}★', 'success')
    return redirect(url_for('room.room_detail', room_id=room_id))


@rv_bp.route('/delete/<int:review_id>', methods=['POST'])
@login_required
def delete_review(review_id):
    """删除评价"""
    review = db.session.get(Review, review_id)
    if review:
        room_id = review.room_id
        db.session.delete(review)
        db.session.commit()
        flash('评价已删除', 'success')
        return redirect(url_for('room.room_detail', room_id=room_id))
    flash('评价不存在', 'danger')
    return redirect(url_for('main.index'))

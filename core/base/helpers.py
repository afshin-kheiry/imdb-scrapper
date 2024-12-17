def paginate(query, page: int, per_page: int):
    return query.limit(per_page).offset((page - 1) * per_page).all()

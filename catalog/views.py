from collections import Counter
from django.shortcuts import render
from .catalogo import ROPA_CATALOGO

CLOTHING_ITEMS = ROPA_CATALOGO


def estimate_size_from_height_weight(h_cm, w_kg):
    """Estimate a size string (XS..XXL) from height (cm) and weight (kg).
    Heurística simple basada en BMI y ajuste por altura.
    """
    if not h_cm or not w_kg:
        return None
    try:
        h_m = h_cm / 100.0
        bmi = w_kg / (h_m * h_m)
    except Exception:
        return None

    # base index from BMI categories
    if bmi < 18.5:
        idx = 1  # S
    elif bmi < 25:
        idx = 2  # M
    elif bmi < 30:
        idx = 3  # L
    else:
        idx = 4  # XL

    # adjust by height: taller people tend to use larger sizes
    if h_cm >= 185:
        idx += 1
    elif h_cm < 160:
        idx -= 1

    # clamp into valid range
    idx = max(0, min(idx, len(SIZE_ORDER) - 1))
    return SIZE_ORDER[idx]

SIZE_ORDER = ['XS', 'S', 'M', 'L', 'XL', 'XXL']


def most_likely_size_from_array(size_array):
    """
    Given an array of talles (e.g. ['S','M','M','L']) return the most likely size.
    Uses mode (most common); if tie, returns the median by order in SIZE_ORDER.
    """
    sizes = [s.strip().upper() for s in size_array if s and isinstance(s, str)]
    if not sizes:
        return None
    counter = Counter(sizes)
    most_common = counter.most_common()
    top_count = most_common[0][1]
    candidates = [s for s, c in most_common if c == top_count]
    if len(candidates) == 1:
        return candidates[0]
    # tie -> choose median according to SIZE_ORDER
    indices = sorted(SIZE_ORDER.index(c) for c in candidates if c in SIZE_ORDER)
    if not indices:
        return candidates[0]
    return SIZE_ORDER[indices[len(indices)//2]]


def find_close_sizes(target_size, radius=1):
    """Return a set of sizes within radius steps of target_size in SIZE_ORDER."""
    if target_size not in SIZE_ORDER:
        return {target_size}
    idx = SIZE_ORDER.index(target_size)
    low = max(0, idx - radius)
    high = min(len(SIZE_ORDER) - 1, idx + radius)
    return set(SIZE_ORDER[low:high+1])


def suggest_items_for_person(height_cm, talle, people_sizes_array=None):
    """
    Core algorithm:
    - Prefer items that explicitly support the given `talle` and whose height range contains `height_cm`.
    - If none found, allow nearby sizes (±1) and prioritize by match score.
    - If a `people_sizes_array` is provided, compute the most common size there and boost items matching it.
    Returns a list of suggested items with a simple score.
    """
    # here `talle` may be an estimated size string
    talle = (talle or '').strip().upper()
    preferred = set()
    if people_sizes_array:
        common = most_likely_size_from_array(people_sizes_array)
        if common:
            preferred.add(common)

    suggestions = []
    for item in CLOTHING_ITEMS:
        size_score = 0
        if talle in item['sizes']:
            size_score += 10
        else:
            # allow close sizes
            if talle in SIZE_ORDER:
                close = find_close_sizes(talle, radius=1)
                if any(s in item['sizes'] for s in close):
                    size_score += 5

        # height score
        if item['min_h'] <= height_cm <= item['max_h']:
            size_score += 5
        else:
            # penalize but still allow
            # distance in cm outside range reduces score
            if height_cm < item['min_h']:
                dist = item['min_h'] - height_cm
            else:
                dist = height_cm - item['max_h']
            size_score -= min(5, dist // 5)

        # boost if item matches most common size of the group
        if preferred and any(s in item['sizes'] for s in preferred):
            size_score += 3

        if size_score > -10:
            suggestions.append({'item': item, 'score': size_score})

    # sort by score descending
    suggestions.sort(key=lambda x: x['score'], reverse=True)
    return suggestions


def index(request):
    # provide sizes and catalog items to the main view
    genders = sorted(list(set(item.get('gender', 'otro') for item in CLOTHING_ITEMS)))

    # If the user provided height/weight/sex via GET, filter the catalog
    display_items = CLOTHING_ITEMS
    selected_height = None
    selected_weight = None
    selected_sex = None
    estimated = None

    if request.method == 'GET' and (request.GET.get('height') or request.GET.get('weight')):
        try:
            selected_height = int(request.GET.get('height', '').strip() or 0)
        except ValueError:
            selected_height = 0
        try:
            selected_weight = float(request.GET.get('weight', '').strip() or 0)
        except ValueError:
            selected_weight = 0

        selected_sex = request.GET.get('sex', '').strip().lower()

        # estimate size and get matching suggestions via the existing algorithm
        estimated = estimate_size_from_height_weight(selected_height, selected_weight)
        suggested = suggest_items_for_person(selected_height, estimated, None)

        # filter by sex if provided
        if selected_sex in ('hombre', 'mujer'):
            suggested = [s for s in suggested if s['item'].get('gender', '').lower() == selected_sex]

        # derive display items from suggestions (ordered)
        display_items = [s['item'] for s in suggested]

    # cart count for header
    cart = request.session.get('cart', [])
    cart_count = len(cart)

    return render(request, 'catalog/index.html', {
        'sizes': SIZE_ORDER,
        'items': CLOTHING_ITEMS,
        'genders': genders,
        'display_items': display_items,
        'selected_height': selected_height,
        'selected_weight': selected_weight,
        'selected_sex': selected_sex,
        'estimated_size': estimated,
        'cart_count': cart_count,
    })


def cart_view(request):
    """Show items in user's session cart."""
    cart = request.session.get('cart', [])
    # map ids to items
    items = []
    for cid in cart:
        for it in CLOTHING_ITEMS:
            if it.get('id') == cid:
                items.append(it)
                break

    total = len(items)
    return render(request, 'catalog/cart.html', {'items': items, 'total': total})


def cart_add(request):
    """Add an item id (POST param `id`) to the session cart and redirect back."""
    if request.method == 'POST':
        try:
            iid = int(request.POST.get('id'))
        except Exception:
            return render(request, 'catalog/cart.html', {'items': [], 'total': 0})

        cart = request.session.get('cart', [])
        if iid not in cart:
            cart.append(iid)
            request.session['cart'] = cart

    # redirect back to index
    from django.shortcuts import redirect
    return redirect(request.POST.get('next', '/'))


def cart_remove(request):
    """Remove an item id (POST param `id`) from the session cart, or clear all if id not given."""
    if request.method == 'POST':
        cart = request.session.get('cart', [])
        try:
            iid = request.POST.get('id')
            if iid:
                iid = int(iid)
                if iid in cart:
                    cart.remove(iid)
            else:
                cart = []
        except Exception:
            cart = cart
        request.session['cart'] = cart

    from django.shortcuts import redirect
    return redirect(request.POST.get('next', '/'))


def cart_checkout(request):
    """Simulate a purchase: on POST, capture cart contents, clear cart and redirect to success."""
    from django.shortcuts import redirect
    if request.method == 'POST':
        cart = request.session.get('cart', [])
        # collect items
        purchased = []
        for cid in cart:
            for it in CLOTHING_ITEMS:
                if it.get('id') == cid:
                    purchased.append(it)
                    break

        # create a mock order id and save summary in session
        import time, uuid
        order = {
            'id': str(uuid.uuid4())[:8],
            'timestamp': int(time.time()),
            'items': [{'id': it['id'], 'name': it['name']} for it in purchased],
            'total_items': len(purchased),
        }
        request.session['last_order'] = order

        # clear cart
        request.session['cart'] = []

        return redirect(request.POST.get('next', '/cart/success/'))

    # If GET, redirect to cart
    return redirect('/cart/')


def cart_success(request):
    order = request.session.get('last_order')
    return render(request, 'catalog/success.html', {'order': order})


def suggestions(request):
    context = {'sizes': SIZE_ORDER}
    if request.method == 'GET':
        try:
            height = int(request.GET.get('height', '').strip() or 0)
        except ValueError:
            height = 0
        # read weight instead of talle
        try:
            weight = float(request.GET.get('weight', '').strip() or 0)
        except ValueError:
            weight = 0

        # estimate a likely size from height and weight and reuse the existing suggestion algorithm
        def estimate_size_from_height_weight(h_cm, w_kg):
            if not h_cm or not w_kg:
                return None
            h_m = h_cm / 100.0
            bmi = w_kg / (h_m * h_m)
            # base index from BMI categories
            if bmi < 18.5:
                idx = 1  # S
            elif bmi < 25:
                idx = 2  # M
            elif bmi < 30:
                idx = 3  # L
            else:
                idx = 4  # XL

            # adjust by height: taller people tend to use larger sizes
            if h_cm >= 185:
                idx += 1
            elif h_cm < 160:
                idx -= 1

            # clamp into valid range
            idx = max(0, min(idx, len(SIZE_ORDER) - 1))
            return SIZE_ORDER[idx]

        estimated = estimate_size_from_height_weight(height, weight)

        suggested = suggest_items_for_person(height, estimated, None)
        
        context.update({
            'height': height,
            'weight': weight,
            'estimated_size': estimated,
            'suggested': suggested,
        })

    return render(request, 'catalog/result.html', context)

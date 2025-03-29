from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Avg
from .models import Category, Product, Cart, CartItem, Wishlist

# Create your views here.


# Product Listing Views
def product_list(request, category_slug=None):
    category = None
    products = Product.objects.filter(is_active=True)

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(categories=category)

    # Search functionality
    query = request.GET.get("q")
    if query:
        products = products.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(categories__name__icontains=query)
        ).distinct()

    # Filtering by price
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")

    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    # Sorting
    sort_by = request.GET.get("sort")
    if sort_by == "price_asc":
        products = products.order_by("price")
    elif sort_by == "price_desc":
        products = products.order_by("-price")
    elif sort_by == "newest":
        products = products.order_by("-created_at")

    context = {
        "category": category,
        "products": products,
        "categories": Category.objects.filter(is_active=True),
    }

    return render(request, "shop/product_list.html", context)


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    related_products = (
        Product.objects.filter(categories__in=product.categories.all())
        .exclude(id=product.id)
        .distinct()[:4]
    )
    reviews = product.reviews.filter(is_approved=True)
    avg_rating = reviews.aggregate(Avg("rating"))["rating__avg"]

    context = {
        "product": product,
        "related_products": related_products,
        "reviews": reviews,
        "avg_rating": avg_rating,
    }

    return render(request, "shop/product_detail.html", context)


# Cart Views
def get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_id = request.session.session_key
        if not session_id:
            request.session.create()
            session_id = request.session.session_key

        cart, created = Cart.objects.get_or_create(session_id=session_id)

    return cart


def cart_detail(request):
    cart = get_or_create_cart(request)
    context = {
        "cart": cart,
    }
    return render(request, "shop/cart.html", context)


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = get_or_create_cart(request)

    # Check for variation selection if POST data exists
    variation_id = request.POST.get("variation_id")
    variation = None
    if variation_id:
        variation = get_object_or_404(product.variations.all(), id=variation_id)

    quantity = int(request.POST.get("quantity", 1))

    # Get or create cart item
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart, product=product, variation=variation, defaults={"quantity": 0}
    )

    # Update quantity
    cart_item.quantity += quantity
    cart_item.save()

    return redirect("shop:cart_detail")


def update_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)

    if request.user.is_authenticated and cart_item.cart.user != request.user:
        return redirect("shop:cart_detail")

    quantity = int(request.POST.get("quantity", 0))

    if quantity > 0:
        cart_item.quantity = quantity
        cart_item.save()
    else:
        cart_item.delete()

    return redirect("shop:cart_detail")


def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)

    if request.user.is_authenticated and cart_item.cart.user != request.user:
        return redirect("shop:cart_detail")

    cart_item.delete()
    return redirect("shop:cart_detail")


# Wishlist Views
@login_required
def wishlist(request):
    wishlist_items = Wishlist.objects.filter(user=request.user)
    context = {
        "wishlist_items": wishlist_items,
    }
    return render(request, "shop/wishlist.html", context)


@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist_item, created = Wishlist.objects.get_or_create(
        user=request.user, product=product
    )

    return redirect("shop:product_detail", slug=product.slug)


@login_required
def remove_from_wishlist(request, wishlist_id):
    wishlist_item = get_object_or_404(Wishlist, id=wishlist_id, user=request.user)
    wishlist_item.delete()

    return redirect("shop:wishlist")

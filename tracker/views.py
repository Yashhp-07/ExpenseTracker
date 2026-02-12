from urllib import request
from . models import Friend, UserRegistration,Expense,FriendExpense,Groups,GroupExpense,GroupExpenseSplit
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse,JsonResponse
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
import random
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from datetime import datetime,date
from django.db.models import Sum, Avg, Q
from django.urls import reverse
from django.db import transaction
from decimal import Decimal,InvalidOperation
from django.core.paginator import Paginator
from django.utils import timezone
from django.contrib.auth.decorators import login_required

# Create your views here.

def index(request):
    return redirect('register')

@never_cache
def register(request):
    # If user is already logged in, redirect to landing page
    if request.session.get('username'):
        return redirect('landing_page')
    # Retrieving the form data and allowing user to register
    if request.method == "POST":
        name = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        c_password = request.POST.get('c_password')

        #validating password and email
        if password != c_password:
            messages.error(request, "Password do not match")
            return redirect('register')
        
        elif UserRegistration.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return redirect('register')
        
        else:
            #Generate OTP
            otp_code = generate_otp()
            
            #Now, before we make another request to server and lose our data stored in the python variables, lets store them in session
            #Storing the session data under temporary keys
            request.session['temp_reg_name'] = name
            request.session['temp_reg_email'] = email
            request.session['temp_reg_password'] = password               #Not safe, we should hash it first and then store it
            request.session['temp_reg_otp'] = otp_code
            
            try:
                send_mail(
                    subject='Your OTP Code',
                    message=f'Hello {name}, your OTP is {otp_code}.',
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[email],
                    fail_silently=False,
                )
                messages.info(request,f"An OTP has been sent to {email}.")
            except Exception as e:
                messages.error(request, f"Failed to send OTP email: {e}")
                #Clear the temporary session data
                request.session.pop('temp_reg_name', None)
                request.session.pop('temp_reg_email', None)
                request.session.pop('temp_reg_password', None)
                request.session.pop('temp_reg_otp', None)
                return redirect('register')

            return redirect('otp_page')
    return render(request, 'tracker/register.html')

@never_cache
def otp_page(request):
    if request.method == "POST":
        entered_otp = request.POST.get('user_otp')                   #Retrieving the OTP entered by user
        generated_otp = request.session.get('temp_reg_otp')         #Retrieving the OTP stored in session

        #Validating the OTP
        if str(entered_otp) == str(generated_otp):
            #Creating a new user in the database
            user = UserRegistration(
                name = request.session.get('temp_reg_name'),
                email = request.session.get('temp_reg_email'),
                password = request.session.get('temp_reg_password'),
            )
            user.save()

            #Setting final session keys
            #Storing user id in session so after registration, login can be bypassed and we have the user_id on the server side.
            request.session['user_id'] = user.id
            request.session['username'] = user.name

            #Removing temp session data
            del request.session['temp_reg_name']
            del request.session['temp_reg_email']
            del request.session['temp_reg_password']
            del request.session['temp_reg_otp']
            
            messages.success(request, "Registration Successful! You can now log in.")
            return redirect('login')

        else:
            messages.error(request, "Invalid OTP. Please try again.")
            return redirect('otp_page')
    return render(request, 'tracker/otp_page.html')

#Helper Function
def generate_otp():
    return random.randint(1000,9999)

@never_cache
def login_page(request):
    # If user is already logged in, redirect to landing page
    if request.session.get('username'):
        return redirect('landing_page')
    

    # Retrieving the form data and allowing user to login
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            #user = UserRegistration.objects.filter(email=email, password=password).exists() # cannot use since it returns a boolean value and does not give access to user id and name
            #Therefore we use this :-
            user = UserRegistration.objects.get(email=email, password=password) # will raise DoesNotExist exception if no user found

            # Storing user info in session
            request.session['user_id'] = user.id
            request.session['username'] = user.name

            messages.success(request, "Login Successful!")
            return redirect('landing_page')
        
        except UserRegistration.DoesNotExist:
            messages.error(request, "Invalid Credentials. Please try again.")
            return redirect('login')
        
    return render(request, 'tracker/login.html')

def logout_page(request):
    request.session.flush()
    messages.info(request, "You have been logged out.")
    return redirect ('login')

@never_cache
def landing_page(request):
    if 'username' not in request.session:
        messages.error(request, "Please log in to access this page.")
        return redirect('login')
    else:
        return render(request, 'tracker/landing_page.html')

#Personal Dashboard
@never_cache
def personal_dashboard(request):
    user_id = request.session.get('user_id')
    if 'username' not in request.session:
        messages.error(request, "Please log in to access this page.")
        return redirect('login')
    
    #fetch Expenses for the logged-in user
    expenses = Expense.objects.filter(user_id=request.session['user_id']).order_by('-date')

    #Get filter values from GET parameters
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    sort_by = request.GET.get('sort_by', '')

   #Apply search filter
    if search_query:
        expenses = expenses.filter(title__icontains=search_query)

    #Apply category filter
    if category_filter:
        expenses = expenses.filter(category=category_filter)

    #Apply sorting
    if sort_by == 'amount_asc':
        expenses = expenses.order_by('amount')
    elif sort_by == 'amount_desc':
        expenses = expenses.order_by('-amount')
    else:
        expenses = expenses.order_by('-date')  # Default sorting by date descending

    #Statistics Section
    total_spent = expenses.aggregate(total = Sum('amount'))['total'] or 0
    avg_spent = expenses.aggregate(avg=Avg('amount'))['avg'] or 0

    #Current month expenses
    current_month = datetime.now().month
    current_year = datetime.now().year
    monthly_expenses = expenses.filter(date__month =current_month, date__year=current_year)
    monthly_total = monthly_expenses.aggregate(total=Sum('amount'))['total'] or 0

    #Category-wise totals
    category_totals = expenses.values('category').annotate(total=Sum('amount')).order_by('-total')

    # --- ADD PAGINATION ---
    paginator = Paginator(expenses, 3) # Show 7 expenses per page
    page_number = request.GET.get('page')
    expenses_page_obj = paginator.get_page(page_number)
    # --- END PAGINATION ---

    context = {
        'expenses_page_obj': expenses_page_obj,
        'username': request.session.get('username'),
        'total_spent': total_spent,
        'avg_spent': avg_spent,
        'monthly_total': monthly_total,
        'category_totals': category_totals,
        'search_query': search_query,
        'category_filter': category_filter,
        'sort_by': sort_by,
    }

    #Passing them to the template
    return render(request, 'tracker/personal.html', context)

def friends_dashboard(request):
    if 'username' not in request.session:
        messages.error(request, "Please log in to access this page.")
        return redirect('login')

    # Fetch user_id from session and list his friends
    user_id = request.session.get('user_id')
    friends = Friend.objects.filter(user_id=user_id)
    print(friends)
    return render(request, 'tracker/friends.html', {'friends': friends})

def friend_details(request, friend_id):
    if 'username' not in request.session:
        messages.error(request, "Please log in to access this page.")
        return redirect('login')

    user_id = request.session.get('user_id')
    user = get_object_or_404(UserRegistration, id=user_id)
    friend = get_object_or_404(UserRegistration, id=friend_id)

    # --- THIS IS THE FIX ---
    # We ONLY query for records the logged-in user created about this friend.
    # The 'Q' object is removed.
    all_expenses = FriendExpense.objects.filter(
        user=user, 
        friend_user=friend
    ).order_by('-date')
    # --- END FIX ---

    # The balance is now a simple SUM of these records.
    total_balance = all_expenses.aggregate(total=Sum('amount_owed'))['total'] or Decimal('0.00')

    # (Optional) Get total amount spent
    total_expenses_sum = all_expenses.aggregate(total=Sum('amount'))['total'] or 0

    # --- NEW: PAGINATION LOGIC ---
    paginator = Paginator(all_expenses, 10) # 10 expenses per page
    page_number = request.GET.get('page')
    expenses_page_obj = paginator.get_page(page_number)
    # --- END OF NEW LOGIC ---

    context = {
        'friend': friend,
        'expenses_page_obj': expenses_page_obj, # Pass the paginated object
        'total_expenses': total_expenses_sum,
        'total_balance': total_balance,       # Pass the correct, simple balance
        'user': user,
    }
    return render(request, 'tracker/friend_details.html', context)

@never_cache
def add_friend(request):
    if request.method == 'POST':
        friend_email = request.POST.get('friend_email')
        print(UserRegistration.objects.values_list('name','email'))
        try:
            friend_user = UserRegistration.objects.get(email=friend_email)
            user = UserRegistration.objects.get(id=request.session.get('user_id'))
            #Create a Friend instance
            #Linking the two users in the Friend model - one as the current user and the other as the friend (Parenthesis logic)
            Friend.objects.create(user=user, friend_user=friend_user)
            messages.success(request, "Friend added successfully!")
            #Send invite email
            try:
                send_mail(
                    subject=f"{user.name} added you as a friend on 'tracker' ",
                    message=f"{user.name} has added you as a friend on 'tracker' to share and manage your expenses together.",
                    from_email='yashp07052004@gmail.com',
                    recipient_list=[friend_user.email],
                    fail_silently=True
                )
            except Exception as e:
                print("Email sending failed", e)
                messages.warning(request, "Friend added, but email failed")
        except UserRegistration.DoesNotExist:
            messages.error(request, "User not found.")
        return redirect('friends_dashboard')
    return render(request, 'tracker/add_friend.html')

    # if 'username' not in request.session:
    #     messages.error(request, "Please log in to access this page.")
    #     return redirect('login')

    # user_id = request.session.get('user_id')
    # user = get_object_or_404(UserRegistration, id=user_id)
    # friend = get_object_or_404(UserRegistration, id=friend_id)

    # # 1. Get the *full list* of expenses for balance calculation
    # all_expenses = FriendExpense.objects.filter(
    #     Q(user=user, friend_user=friend) |
    #     Q(user=friend, friend_user=user)
    # ).order_by('-date')

    # # --- THIS IS THE BALANCE FIX ---
    # # 2. Calculate balance from YOUR perspective
    # my_balance_val = all_expenses.filter(
    #     user=user
    # ).aggregate(total=Sum('amount_owed'))['total'] or 0.0

    # # 3. Calculate balance from your FRIEND'S perspective
    # their_balance_val = all_expenses.filter(
    #     user=friend
    # ).aggregate(total=Sum('amount_owed'))['total'] or 0.0
    
    # # 4. The true balance is your perspective minus their perspective
    # total_balance = Decimal(my_balance_val) - Decimal(their_balance_val)
    # # --- END OF BALANCE FIX ---

    # # (Optional) Get total amount spent
    # total_expenses_sum = all_expenses.aggregate(total=Sum('amount'))['total'] or 0

    # # --- NEW: PAGINATION LOGIC ---
    # paginator = Paginator(all_expenses, 10) # 10 expenses per page
    # page_number = request.GET.get('page')
    # expenses_page_obj = paginator.get_page(page_number)
    # # --- END OF NEW LOGIC ---

    # context = {
    #     'friend': friend,
    #     'expenses_page_obj': expenses_page_obj, # Pass the paginated object
    #     'total_expenses': total_expenses_sum,
    #     'total_balance': total_balance,       # Pass the correct balance
    #     'user': user,
    # }
    # return render(request, 'tracker/friend_details.html', context)

#changes
@never_cache
def remove_friend(request,friend_id):
    if 'username' not in request.session:
        messages.error(request, "Please log in to access this page.")
        return redirect('login')
    
    friend = get_object_or_404(UserRegistration, id=friend_id)
    user_id = request.session.get('user_id')

    if request.method == 'POST':
        #Remove both directions
        Friend.objects.filter(user_id=user_id, friend_user_id=friend_id).delete()
        Friend.objects.filter(user_id=friend_id, friend_user_id=user_id).delete()
        messages.success(request, "Friend removed")
        return redirect('friends_dashboard')
    
    return render(request, 'tracker/remove_friend.html', {'friend': friend})

@never_cache
def add_expense_with_friend(request, friend_id):
    if 'username' not in request.session:
        return redirect('login')
    friend = UserRegistration.objects.get(id=friend_id)
    user = UserRegistration.objects.get(id=request.session.get('user_id'))
    if request.method == 'POST':
        title = request.POST.get('title')
        category = request.POST.get('category')
        amount = float(request.POST.get('amount'))
        description = request.POST.get('description', '')
        try:
            paid_by_id = int(request.POST.get('paid_by'))
            paid_by = UserRegistration.objects.get(id=paid_by_id)
        except (TypeError, ValueError, UserRegistration.DoesNotExist):
            messages.error(request,"Invalid payer selected")
            return redirect(request.path)
        #Split logic for now-->equal split
        amount_owed = amount / 2
        FriendExpense.objects.create(
            user=user,
            friend_user=friend,
            title=title,
            amount=amount,
            category=category,
            description=description,
            paid_by=paid_by,
            amount_owed=amount_owed,
        )
        messages.success(request, "Expense added successfully!")
        return redirect('friend_details', friend_id=friend_id)
    return render(request, 'tracker/add_expense_with_friend.html', {'friend': friend, 'user':user})

def expense_details(request, friend_id):
    user_id = request.session.get('user_id')
    user = UserRegistration.objects.get(id=user_id)
    friend = UserRegistration.objects.get(id=friend_id)
    title = request.GET.get('title', '')
    description = request.GET.get('description', '')
    category = request.GET.get('category', '')
    amount = (request.GET.get('amount', 0))
    paid_by = int(request.GET.get('paid_by', user_id))
    return render(request, 'tracker/expense_details.html', {
        'user': user,
        'friend': friend,
        'title': title,
        'description': description,
        'category': category,
        'amount': amount,
        'paid_by': paid_by,
    })

def save_split_expense(request, friend_id):
    if request.method == 'POST':
        try:
            user_id = request.session.get('user_id')
            if not user_id:
                # Handle case where user is not logged in
                return JsonResponse({'status': 'error', 'message': 'User not authenticated.'}, status=401)
            
            # Get data from the POST request
            amount = float(request.POST.get('amount'))
            friend = UserRegistration.objects.get(id=friend_id)
            user = UserRegistration.objects.get(id=user_id)
            user_share = float(request.POST.get('user_share'))
            friend_share = float(request.POST.get('friend_share'))
            paid_by_id = int(request.POST.get('paid_by'))
            paid_by = UserRegistration.objects.get(id=paid_by_id)

            # Determine who owes what
            # If the current user paid, the friend owes their share.
            # If the friend paid, the current user owes their share.
            amount_owed_by_friend_to_user = friend_share if paid_by_id == user_id else -user_share

            # Save the new expense record
            FriendExpense.objects.create(
                user=user,
                friend_user=friend,
                title=request.POST.get('title'),
                amount=amount,
                category=request.POST.get('category'),
                description=request.POST.get('description', ''),
                paid_by=paid_by,
                # amount_owed logic corrected to handle debt direction
                # Positive value means friend owes user, negative means user owes friend.
                amount_owed=amount_owed_by_friend_to_user 
            )

            messages.success(request, "Expense split and saved!")
            
            # **THE FIX**: Return a JSON response with the redirect URL
            redirect_url = reverse('friend_details', kwargs={'friend_id': friend_id})
            return JsonResponse({'status': 'success', 'redirect_url': redirect_url})

        except UserRegistration.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Invalid user or friend ID.'}, status=404)
        except Exception as e:
            # Catch other potential errors (e.g., float conversion)
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    # Handle non-POST requests
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)

@never_cache
def delete_friend_expense(request, expense_id):
    if 'username' not in request.session:
        messages.error(request,"Please login to access this page.")
        return redirect('login')
    
    user_id = request.session.get('user_id')

    try:
        #Get the expense object
        expense = get_object_or_404(FriendExpense, pk=expense_id)
        #Get the friend_id that we need for redirect and template rendering
        friend_id_for_redirect = expense.friend_user.id
    except FriendExpense.DoesNotExist:
        messages.error(request, "Expense not found.")
        return redirect('friends_dashboard')

    if request.method == 'POST':
        try:
            expense.delete()
            messages.success(request, "Expense deleted successfully.")
            return redirect('friend_details', friend_id=friend_id_for_redirect)

        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
            return redirect('friend_details', friend_id=friend_id_for_redirect)

    context = {
        'expense': expense,
        'expense_id': expense_id,
        'friend_id': friend_id_for_redirect,
    }
    return render(request,'tracker/delete_friend_expense.html', context)

#Groups Dashboard
def groups_dashboard(request):
    if 'username' not in request.session:
        messages.error(request, "Please log in to access this page.")
        return redirect('login')
    user_id = request.session.get('user_id')
    user = UserRegistration.objects.get(id=user_id)

    #Get the selected filter option from GET parameters
    # selected_filter = request.GET.get('filter', 'none')

    groups = Groups.objects.filter(members=user)

    #Total amt user owes across all groups
    # overall_owe = (
    #     GroupExpense.objects.filter(
    #         Q(owed_by=user) & ~Q(balance__lt=0) #user owes negative balance
    # ).aggregate(total_owed=Sum('balance'))['total'] or 0
    # )
    # overall_owe = abs(overall_owe)

    #Filtering Logic
    # if selected_filter == 'balances':
    #     groups = groups.filter(groupexpense__balance__ne=0).distinct()
    # elif selected_filter == 'you_owe':
    #     groups = groups.filter(groupexpense__owed_by=user, groupexpense__balance__lt=0).distinct()
    # elif selected_filter == 'you_are_owed':
    #     groups = groups.filter(groupexpense__owed_by=user, groupexpense__balance__gt=0).distinct()
    # 'none' → no filter applied

    #Get filter from Dropdown
    filter_option = request.GET.get('filter', 'None')

    if filter_option == 'None':
        filtered_groups = groups
    else:
        filtered_groups = groups


    overall_owe = 0  # Placeholder for overall owe calculation

    context = {
        'groups': groups,
        'filter_option': filter_option,
        'overall_owe': overall_owe,
    }
    return render(request, 'tracker/groups.html', context)

@never_cache
def create_group(request):
    if 'username' not in request.session:
        messages.error(request, "Please log in to access this page.")
        return redirect('login')
    
    user_id = request.session.get('user_id')
    user = UserRegistration.objects.get(id=user_id)

    if request.method == 'POST':
        name = request.POST.get('name')
        category = request.POST.get('category')

        #Why if
        if name and category:
            group = Groups.objects.create(name=name, category=category, created_by=user)
            messages.success(request, "Group created successfully!")
            return redirect('group_details', group_id=group.id)
        else:
            messages.error(request,"Please fill all fields.")
    return render(request, 'tracker/create_group.html')

@never_cache
def remove_from_group(request, group_id):
    if 'username' not in request.session:
        messages.error(request, "Please log in to access this page.")
        return redirect('login')
    user_id = request.session.get('user_id')
    user = UserRegistration.objects.get(id=user_id)
    group = get_object_or_404(Groups, id=group_id)
    #Removes current user's membership from the group.
    if request.method == 'POST':
        # Remove the user's membership from the group
        group.members.remove(user)
        
        # Optional: If the user was the last member, delete the group entirely
        if group.members.count() == 0:
            group.delete()
            messages.info(request, f"You left '{group.name}', and the group has been deleted as you were the last member.")
        
        messages.success(request, f"You have successfully left the group '{group.name}'.")   
        return redirect('groups')
    
    return render(request, 'tracker/leave_group.html', {'group':group})

def group_details(request, group_id):
    if 'username' not in request.session:
        messages.error(request, "Please log in to access this page.")
        return redirect('login')

    #Get current user to pass to the template for checks
    user_id = request.session.get('user_id')
    user = UserRegistration.objects.get(id=user_id)
    group = get_object_or_404(Groups, id=group_id)
    all_members = group.members.all()

    #We get the ful unsliced lists for balance calculation
    #1. Fetch all group expenses with related splits
    all_group_expenses = GroupExpense.objects.filter(group=group).prefetch_related('splits', 'paid_by').order_by('-date')

    #2. Get 1-on-1 Friend Expenses (payments) only for this group
    all_friend_expenses = FriendExpense.objects.filter(
        group=group,                         #only Get payments linked to this group
    ).order_by('-date').select_related('user', 'friend_user', 'paid_by')

    #Phase 4 Balance calculation logic
    balance_summary = []

    #Loop all members except user
    for member in all_members:
        if member.id == user.id:
            continue  # Skip current user

        #Part 1: Calculate balance from Group Expenses
        # Use Decimal to prevent errors with None
        #Calculate what this 'member' owes to 'user'
        member_owes_user = GroupExpenseSplit.objects.filter(
            expense__in=all_group_expenses,                   #In this group's expenses
            expense__paid_by=user,                  #Paid by current user
            user=member                             #For this specific member's share
        ).aggregate(total=Sum('amount_owed'))['total'] or Decimal("0.00") #FIX : Use Decimal

        #Calculate what 'user' owes to this 'member'
        user_owes_member = GroupExpenseSplit.objects.filter(
            expense__in=all_group_expenses,                   #In this group's expenses
            expense__paid_by=member,                #Paid by this specific member
            user=user                               #For current user's share
        ).aggregate(total=Sum('amount_owed'))['total'] or Decimal("0.00") #FIX : Use Decimal

        #Calculate net balance from user's perspective
        group_balance = member_owes_user - user_owes_member  #This is Decimal

        #Part 2 Calculate balance from 1-on-1 Friend Expenses
        #FIX : Check records 'user' created about 'member'
        #Assumes the amount_owed in FriendExpense is always from user perspective
        #Balance from records 'user' created about 'member'
        # Friend balance now filtered by group
        friend_balance_user_created_float = all_friend_expenses.filter(
            user=user,
            friend_user=member
        ).aggregate(total=Sum('amount_owed'))['total'] or 0.0

        #FIX : Check records 'member' created about 'user'
        #Balance from records 'member' created about 'user'
        #Here amount_owed is from 'member' perspective, so we invert the sign
        friend_balance_member_created_float = all_friend_expenses.filter(
            user=member,
            friend_user=user
        ).aggregate(total=Sum('amount_owed'))['total'] or 0.0

        #The total 1-on-1 balance is our records + the inverse records from friends
        total_friend_balance = Decimal(friend_balance_user_created_float) - Decimal(friend_balance_member_created_float)

        #Part 3: Calculate True net balance
        #Safe now : Decimal + Decimal
        net_balance = group_balance + total_friend_balance

        #Only shows members with non-zero balances
        if abs(net_balance) > 0.01:  # Small threshold to avoid floating-point issues   
            balance_summary.append({
                'member': member,
                'balance': net_balance
            })

    #Pagination Logic
    # Paginate Group Expenses (10 per page)
    group_paginator = Paginator(all_group_expenses, 10)
    page_number = request.GET.get('page')
    expenses_page_obj = group_paginator.get_page(page_number)

    # Paginate Friend Expenses (5 per page)
    friend_paginator = Paginator(all_friend_expenses, 5)
    pay_page_number = request.GET.get('pay_page')
    friend_expenses_page_obj = friend_paginator.get_page(pay_page_number)
    # --- END OF NEW LOGIC ---

    context = {
        'group': group,
        'expenses_page_obj': expenses_page_obj,
        'friend_expenses_page_obj': friend_expenses_page_obj,
        'current_user': user,
        'balance_summary': balance_summary,
        'members':group.members.all(), #Passing all members to template for if checks
    }
    return render(request, 'tracker/group_details.html', context)

@never_cache
def add_members(request, group_id):
    #Handles adding new members to a group from the user's friend list
    group = get_object_or_404(Groups, id=group_id)
    user = UserRegistration.objects.get(id=request.session.get('user_id'))

    if request.method == 'POST':
        members_to_add_ids = request.POST.getlist('members')
        for member_id in members_to_add_ids:
            friend_to_add = UserRegistration.objects.get(id=member_id)
            group.members.add(friend_to_add)
        messages.success(request, "New members added successfully!")
        return redirect('group_details', group_id=group.id)

    # GET Request Logic:
    current_members = group.members.all()
    friends = Friend.objects.filter(user=user)

    # Create a list of friends who are not already in the group
    available_friends = []
    for friend_relation in friends:
        if friend_relation.friend_user not in current_members:
            available_friends.append(friend_relation.friend_user)
    
    context = {
        'group': group,
        'available_friends': available_friends
    }
    return render(request, 'tracker/add_members.html', context)

@never_cache
def add_group_expense(request, group_id):
    """A placeholder view to render the 'Add Group Expense' page."""
    if 'username' not in request.session:
        messages.error(request, "Please log in to access this page.")
        return redirect('login')
    
    user_id = request.session.get('user_id')
    user = UserRegistration.objects.get(id=user_id)
    group = get_object_or_404(Groups, id=group_id)
    
    context = {'group': group}
    return render(request, 'tracker/add_group_expense.html', context)

@never_cache
def delete_group_expense(request, expense_id):
    if 'username' not in request.session:
        messages.error(request, "Please login to access this page.")
        return redirect('login')
    
    #Get user_id and expense outside the try to send them into context to the HTML with the GET request.
    user_id = request.session.get('user_id')
    expense = get_object_or_404(GroupExpense.objects.select_related('group'), pk=expense_id)
    try:
        #Get the group ID that we need for redirect and template rendering
        group_id_for_redirect = expense.group.id
    except GroupExpense.DoesNotExist:
        messages.error(request, "Expense not found.")
        return redirect('groups_dashboard')
    
    if request.method == 'POST':
        try:
            expense.delete()
            messages.success(request, "Group expense deleted successfully.")
            return redirect('group_details', group_id=group_id_for_redirect)
        
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
            return redirect('group_details', group_id=group_id_for_redirect)
    
    context = {
        'expense': expense,
        'expense_id': expense_id,
        'group_id': group_id_for_redirect,
    }
    return render(request,'tracker/delete_group_expense.html', context)

#New and most complex view to save group expenses
def save_group_split_expense(request, group_id):
    if request.method == 'POST':
        try:
            # 1. Get user and group
            user_id = request.session.get('user_id')
            if not user_id:
                return JsonResponse({'status': 'error', 'message': 'User not authenticated.'}, status=401)
            
            group = get_object_or_404(Groups, id=group_id)
            # paid_by_user = get_object_or_404(UserRegistration, id=request.POST.get('paid_by'))

            #New validation By Gemini
            paid_by_id = request.POST.get('paid_by')
            if not paid_by_id:
                # This error will be shown to the user if the JS somehow fails
                return JsonResponse({'status': 'error', 'message': '"Paid by" field is missing. Please select who paid.'}, status=400)
            
            try:
                # We also wrap the 'get' in a try/except to be safe
                paid_by_user = get_object_or_404(UserRegistration, id=int(paid_by_id))
            except (ValueError, TypeError, UserRegistration.DoesNotExist):
                return JsonResponse({'status': 'error', 'message': 'Invalid "Paid by" user selected.'}, status=400)
            # ** NEW VALIDATION ENDS HERE **

            # Check if the logged-in user is part of this group (optional but good security)
            if not group.members.filter(id=user_id).exists():
                 return JsonResponse({'status': 'error', 'message': 'You are not a member of this group.'}, status=403)

            # 2. Get basic expense data
            total_amount = float(request.POST.get('amount'))
            title = request.POST.get('title')

            # 3. Use a transaction for safety
            # This ensures we either create the expense AND all its splits, or nothing.
            with transaction.atomic():
                # 4. Create the main GroupExpense
                new_expense = GroupExpense.objects.create(
                    group=group,
                    paid_by=paid_by_user,
                    title=title,
                    amount=total_amount,
                )

                # 5. Loop through group members to get their shares
                group_members = group.members.all()
                splits_to_create = []
                total_share_check = 0.0

                for member in group_members:
                    # This key matches the 'name' attribute in the form's hidden fields:
                    # name="share_{{ member.id }}"
                    share_key = f'share_{member.id}' 
                    
                    # Get the share amount from the POST data, default to 0.0
                    member_share = float(request.POST.get(share_key, 0.0))

                    # This is the user's share of the bill (what they are responsible for)
                    if member_share > 0:
                        total_share_check += member_share
                        splits_to_create.append(
                            GroupExpenseSplit(
                                expense=new_expense,
                                user=member,
                                amount_owed=member_share  # This model correctly stores the share
                            )
                        )
                
                # 6. Validation: Check if splits add up to the total
                # We use a small tolerance (e.g., 0.01) for floating-point math errors
                if abs(total_share_check - total_amount) > 0.01:
                    # This error will automatically roll back the transaction
                    raise Exception(f"Split amounts (Rs {total_share_check:.2f}) do not match total expense (Rs {total_amount:.2f}).")

                # 7. Save all splits to the database at once
                GroupExpenseSplit.objects.bulk_create(splits_to_create)

            # 8. Success: Send JSON response back to the JavaScript
            messages.success(request, 'Expense saved successfully!')
            redirect_url = reverse('group_details', kwargs={'group_id': group_id})
            return JsonResponse({'status': 'success', 'redirect_url': redirect_url})

        except (UserRegistration.DoesNotExist, Groups.DoesNotExist):
            return JsonResponse({'status': 'error', 'message': 'Invalid user or group.'}, status=404)
        except Exception as e:
            # Catch any other error (like float conversion, validation, etc.)
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    # Handle non-POST requests
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)


#Activity Dashboard
def activity_dashboard(request):
    if 'username' not in request.session:
        messages.error(request, "Please log in to access this page.")
        return redirect('login')
    
    user_id = request.session.get('user_id')
    user = get_object_or_404(UserRegistration, id=user_id)

    activity_list = []

    # --- 1. Get Friend Expenses (including Payments) ---
    # Fetch records where the user is either the creator or the friend involved
    friend_expenses = FriendExpense.objects.filter(
        Q(user=user) | Q(friend_user=user)
    ).select_related('user', 'friend_user', 'paid_by', 'group').order_by('-date') # Use 'date' field

    for item in friend_expenses:
        # Determine the date field (assuming 'date' exists, fallback to 'created_at')
        activity_date = getattr(item, 'date', getattr(item, 'created_at', None))
        if activity_date:
            activity_list.append({
                'date': activity_date,
                'type': 'friend_expense',
                'details': item
            })

    # --- 2. Get Group Expenses ---
    # Fetch expenses from groups the user is a member of
    group_expenses = GroupExpense.objects.filter(
        group__members=user
    ).select_related('group', 'paid_by').order_by('-date') # Use 'date' field

    for item in group_expenses:
        activity_date = getattr(item, 'date', getattr(item, 'created_at', None))
        if activity_date:
            activity_list.append({
                'date': activity_date,
                'type': 'group_expense',
                'details': item
            })

    # --- 3. Get Group Creations ---
    # Fetch groups where the user is a member (created or added)
    # Note: Need a 'created_at' field on the Groups model for sorting
    groups_involved = Groups.objects.filter(members=user).order_by('-created_at') # Assumes 'created_at' field

    for item in groups_involved:
        # Use group's creation date
        if hasattr(item, 'created_at'):
            activity_list.append({
                'date': item.created_at,
                'type': 'group_creation',
                'details': item
            })

    # --- (Optional) 4. Get Personal Expenses ---
    # personal_expenses = Expense.objects.filter(user=user).order_by('-date')
    # for item in personal_expenses:
    #     activity_list.append({
    #         'date': item.date,
    #         'type': 'personal_expense',
    #         'details': item
    #     })

    # --- 5. Sort the combined list ---
    # Sort by date, most recent first. Handles potential None dates.
    sorted_activities = sorted(
    [act for act in activity_list if act.get('date')],
    key=lambda x: (
        # Convert date objects to naive datetime at midnight
        datetime.combine(x['date'], datetime.min.time()) if isinstance(x['date'], date) and not isinstance(x['date'], datetime)
        # Convert aware datetime objects to naive
        else timezone.make_naive(x['date']) if timezone.is_aware(x['date'])
        # Otherwise, it's already naive, use it as is
        else x['date']
    ),
    reverse=True
)

    # --- ADD PAGINATION ---
    paginator = Paginator(sorted_activities, 10) # Show 10 activities per page
    page_number = request.GET.get('page')
    activities_page_obj = paginator.get_page(page_number)
    # --- END PAGINATION ---

    context = {
        'activities_page_obj': activities_page_obj,
        'current_user': user # Pass user for template logic
    }
    return render(request, 'tracker/activity.html', context)


#Settle Up Balances
#for friend and group 
@never_cache
def record_payment(request, friend_id):
    if request.method == 'POST':
        try:
            user_id = request.session.get('user_id')
            if not user_id:
                return redirect('login') # Or your login page

            user = get_object_or_404(UserRegistration, id=user_id)
            friend = get_object_or_404(UserRegistration, id=friend_id)
            
            amount = float(request.POST.get('amount'))
            payer_id = int(request.POST.get('payer'))
            
            # --- ADD THIS BLOCK ---
            # Check if a group_id was sent with the form
            group_id = request.POST.get('group_id')
            group_instance = None
            if group_id:
                try:
                    group_instance = Groups.objects.get(id=group_id)
                except Groups.DoesNotExist:
                    pass # Ignore if group doesn't exist
            # --- END ADDED BLOCK ---

            # Determine who the receiver is
            if payer_id == user_id:
                paid_by_user = user
                receiver_name = friend.name
            else:
                paid_by_user = friend
                receiver_name = user.name

            # key logic
            if payer_id == user_id:
                amount_to_save = amount  # Positive: Friend "owes" this payment back
            else:
                amount_to_save = -amount # Negative: User "owes" this payment back
            # --- End of logic ---
            
            #This creates the 1-on-1 payment record
            # Create the payment as a FriendExpense
            FriendExpense.objects.create(
                user=user,  # The logged-in user is always the 'owner' of the record
                friend_user=friend,
                title="Payment",
                description=f"{paid_by_user.name} paid {receiver_name}",
                amount=amount,
                category="Payment",
                paid_by=paid_by_user,
                amount_owed=amount_to_save,  # This is the calculated balance shift
                group=group_instance  # Link to group if provided
            )
            
            messages.success(request, "Payment recorded successfully!")

        except Exception as e:
            messages.error(request, f"Error recording payment: {e}")

        #New redirect Logic
        #Check if form sent a 'redirect_url'
        redirect_url = request.POST.get('redirect_url')
        if redirect_url:
            return redirect(redirect_url)
        else:
            return redirect('friend_details', friend_id=friend_id)

    return redirect('personal_dashboard')

#CRUD
@never_cache
def add_expense(request):
    user_id = request.session.get('user_id')
    if 'username' not in request.session or not user_id:
        messages.error(request, "Please log in to access this page.")
        return redirect('login')
    
    #Get logged in user from session to know which user is adding the expense
    user = UserRegistration.objects.get(id=user_id)
    if request.method == 'POST':


        #Get form data
        title = request.POST.get('title')
        amount = request.POST.get('amount')
        category = request.POST.get('category')
        date = request.POST.get('date')

        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError("Amount must be greater than 0.")
        except (ValueError,TypeError,InvalidOperation):
            messages.error(request, "Please enter a valid amount greater than 0.")
            context = {
                'title': title,
                'amount': amount,
                'category': category,
                'date': date,
            }
            return render(request, 'tracker/add_expense.html', context)
        

        #Save to DB
        expense = Expense(
            user=user,
            title=title,
            amount=amount,
            category=category,
            date=datetime.strptime(date, "%Y-%m-%d").date(),  # Convert string to date object
        )
        expense.save()

        #Show success message
        messages.success(request, "Expense added successfully!")
        return redirect('personal_dashboard')
    
    # GET request - pass an empty dictionary for 'expense'
    # to avoid errors on initial load
    context = {
        'expense': {
            'title': '', 'amount': '', 'category': 'Food', 'date': '', 'description': ''
        }
    }

    return render(request, 'tracker/add_expense.html', context)

@never_cache
def edit_expense(request, expense_id):
    if 'username' not in request.session:
        messages.error(request, "Please log in to access this page.")
        return redirect('login')
    
    #Fetch the expense to be edited
    expense = get_object_or_404(Expense, id=expense_id, user_id=request.session['user_id'])

    if request.method == 'POST':
        expense.title = request.POST.get('title')
        expense.amount = request.POST.get('amount')
        expense.category = request.POST.get('category')
        expense.date = request.POST.get('date')
        expense.save()
        messages.success(request, "Expense updated successfully!")
        return redirect('personal_dashboard')

    return render(request, 'tracker/edit_expense.html', {'expense': expense})

def delete_expense(request, expense_id):
    if 'username' not in request.session:
        messages.error(request, "Please log in to access this page.")
        return redirect('login')
    
    expense = get_object_or_404(Expense, id=expense_id, user_id=request.session['user_id'])

    if request.method == 'POST':
        expense.delete()
        messages.success(request, "Expense deleted successfully!")
        return redirect('personal_dashboard')

    return render(request, 'tracker/delete_expense.html', {'expense': expense})

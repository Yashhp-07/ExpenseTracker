from django.db import models
from django.contrib.auth.models import User

# Create your models here.

# Models are python classes that represent database tables.
# Each attribute of the class is a column in the table.

# Manual User Registration Model

class UserRegistration(models.Model):
    name = models.CharField(max_length=100)
    email = models.CharField(max_length=100,unique=True)
    password = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} - {self.email}"
    
#Expense Model for CRUD 
class Expense(models.Model):
    user = models.ForeignKey(UserRegistration, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    amount = models.FloatField()
    category = models.CharField(max_length=50)
    date = models.DateField()

    #String representation of the expense (for admin and debugging)
    def __str__(self):
        return f"{self.title} - {self.amount}"
    
class Friend(models.Model):
    user = models.ForeignKey(UserRegistration, on_delete=models.CASCADE, related_name='owner')
    friend_user = models.ForeignKey(UserRegistration, on_delete=models.CASCADE, related_name='friend')
    created_at = models.DateTimeField(auto_now_add=True)


#Creating Reciprocal Friendship
#When a friendship is created, ensure that the reverse friendship also exists.
#Because if A is friend with B, its one-way friendship.
#Only A can see and interact with expenses of B, but B cannot see A's expenses.

#You can enforce this logic in the save method of the Friend model.
#When a Friend instance is saved, check if the reverse friendship exists.
#If not, create it.
#This ensures that friendships are always mutual.
#It creates -> Mutual collaboration, Consistent user experience, Better data integrity.
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Ensure mutual friendship
        if not Friend.objects.filter(user=self.friend_user, friend_user=self.user).exists():
            Friend.objects.create(user=self.friend_user, friend_user=self.user)

    def __str__(self):
        return f"{self.user.name} is friends with {self.friend_user.name}"
    
class FriendExpense(models.Model):
    user = models.ForeignKey(UserRegistration, on_delete=models.CASCADE, related_name='friend_expense_owner')
    friend_user = models.ForeignKey(UserRegistration, on_delete=models.CASCADE, related_name='friend_expense_friend')
    title = models.CharField(max_length=200)
    amount = models.FloatField()
    category = models.CharField(max_length=80)
    date = models.DateField(auto_now_add=True)
    description = models.TextField(blank=True,null=True)
    paid_by = models.ForeignKey(UserRegistration, on_delete=models.CASCADE, related_name='paid_expenses',blank=True,null=True)
    amount_owed = models.FloatField(default=0) #Amount the user owes
    #this will "tag" the payment to a group if needed.
    group = models.ForeignKey('Groups', on_delete=models.SET_NULL, blank=True, null=True, related_name="payments")

    def __str__(self):
        return f"{self.title} - {self.amount} between {self.user.name} and {self.friend_user.name}"

class Groups(models.Model):
    CATEGORY_CHOICES = [
        ('Trip', 'Trip'),
        ('Home', 'Home'),
        ('Couple', 'Couple'),
        ('Other', 'Other'),
    ]

    name = models.CharField(max_length=100)
    category = models.CharField(max_length=80,choices=CATEGORY_CHOICES)
    created_by = models.ForeignKey(UserRegistration, on_delete=models.CASCADE, related_name='created_groups')
    members = models.ManyToManyField(UserRegistration, related_name='groups')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args,**kwargs)
        #Ensure creator is always a member
        self.members.add(self.created_by)

    def __str__(self):
        return f"{self.name} ({self.category})"
    
class GroupExpense(models.Model):
    group = models.ForeignKey(Groups, on_delete=models.CASCADE, related_name='expenses')
    paid_by = models.ForeignKey(UserRegistration, on_delete=models.CASCADE, related_name='group_paid_expenses')
    title = models.CharField(max_length=200)
    amount = models.FloatField()
    category = models.CharField(max_length=80)
    date = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    #Optional helper field to total balances cached
    total_split_done = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} - {self.amount} in group {self.group.name}"


#Split of each group expense among members to track who owes whom
class GroupExpenseSplit(models.Model):
    expense = models.ForeignKey(GroupExpense, on_delete=models.CASCADE, related_name="splits")
    user = models.ForeignKey(UserRegistration, on_delete=models.CASCADE, related_name="group_expense_splits")
    amount_owed = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.name} owes {self.amount_owed} for {self.expense.title}"

# Login fucntion for superadmin
class adminLogin(TemplateView):
	template_name = 'login.html'
	def get(self,request):
		return render(request,self.template_name)
	def post(self,request):
		form = forms.adminLoginForm(request.POST)
		if form.is_valid():
			email    = form.cleaned_data.get('email')
			password = form.cleaned_data.get('password')

			user = authenticate(username=email, password=password)
			if user:
					print('yes')
					login(request, user)
					messages.success(request, "Login successfully")
					return redirect('/dashboard')

			else:
				messages.success(request, "Invalid email and password.")
				return render(request, self.template_name)
		else:
			return render(request, 'login', {'form': form})

#This function is used for Forget admin password
class adminForgetPassword(TemplateView):
	template_name = 'forgot-password.html'
	def get(self,request):
		return render(request,self.template_name)
	
	def post(self,request):
		form = forms.adminforgetpassword(request.POST)
		if form.is_valid():
			email =  form.cleaned_data.get('email')
			admin_obj = SuperAdmin.objects.filter(email = email).first()
			ran_num = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(12)])
			baselink =  '/forgot-admin/' + str(admin_obj.email) + '/' + ran_num
			completelink = str(settings.BASE_URL) + baselink
			admin_obj.forgotPasswordLink = baselink
			admin_obj.save()            
			subject = 'Forgot Password'
			html_message = render_to_string('forget_admin_password_email.html', {'link': completelink})
			plain_message = html_message
			from_email = settings.EMAIL_HOST_USER
			to = email
			mail.send_mail(subject, plain_message, from_email, [to], html_message=html_message)
			messages.success(request, "A link has been successfully sent to your mail.")
			return redirect('/admin-forget-password')
		else:
			return render(request, self.template_name, {'form': form})
		

# This function is used for refund the money
class RefundMoneyList(TemplateView):
	template_name = 'refund_money_list.html'
	@method_decorator(login_required(login_url='/'))
	def get(self,request):
		admin_obj = SuperAdmin.objects.filter(user=request.user.id).first()
		data_obj = AdminRefundRequest.objects.filter(end_date__isnull = True).order_by('-id')
		search_post = request.GET.get('search')
		refund_date = request.GET.get('refund_date')
		time = "11:59:59"
		lookups = Q()

		if refund_date:
			date_string = str(refund_date) 
			refund_date_time = make_aware(datetime.fromisoformat(date_string))
			lookups.add(Q(created_at__date=refund_date_time), Q.AND)

		if search_post:
			lookups.add(Q(booking__fortune_teller__first_name__icontains=search_post)|Q(booking__fortune_teller__last_name__icontains=search_post)|Q(booking__seer_user__first_name__icontains=search_post)|Q(booking__seer_user__last_name__icontains=search_post)|Q(booking__service__service_name__icontains=search_post), Q.AND)


		data_obj = AdminRefundRequest.objects.filter(lookups,end_date__isnull = True).order_by('-id')

		paginator = Paginator(data_obj, 10)
		page_number = request.GET.get('page')
		refund_obj = paginator.get_page(page_number)

		return render(request,self.template_name,locals())
	

# This function is used for change admin password
class AdminResetPassword(TemplateView):
	template_name = 'admin_reset_password.html'
	@method_decorator(login_required(login_url='/'))
	def get(self,request):
		admin_obj = SuperAdmin.objects.filter(user=request.user.id).first()
		return render(request,self.template_name,locals())

	def post(self,request):
		try:
			form = forms.change_password_form(request.POST)
			if form.is_valid():
				password = request.POST.get("confirmPassword")
				user     = User.objects.get(email=request.user.email)
				user.set_password(password)
				user.save()
				logout(request)
				messages.info(request, 'You have successfully reset your password')
				return redirect('/')
			else:
				return render(request, 'admin_reset_password.html', {'form': form})
		except Exception as e:
			messages.warning(request, "Something went wrong.Please try again.")
			return redirect('dashboard')   

#This function is used for export the csv file 
class ExportUserCsvReport(View):
	def get(self,request):
		queryset = (
			FortuneAppointmentBook.objects
			.values('seer_user__id','seer_user__first_name','seer_user__last_name','seer_user__email','seer_user__primary_image','seer_user__created_at','seer_user__status')
			.annotate(total_appointments=Count('seer_user'))
			.order_by('seer_user')
		)
		response = HttpResponse(content_type='text/csv')
		response['Content-Disposition'] = 'attachment; filename="user_report.csv"'
		writer = csv.writer(response)
		writer.writerow(['User Id', 'User Name', 'User Email' ,'User Image', 'User Created Date','User Status','Booked Appointments'])

		# Write the data rows
		for item in queryset:
			writer.writerow([item['seer_user__id'], item['seer_user__first_name'] + ' ' + item['seer_user__last_name'], item['seer_user__email'] ,item['seer_user__primary_image'], item['seer_user__created_at'], item['seer_user__status'], item['total_appointments']])

		return response

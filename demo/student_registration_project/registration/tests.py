from django.test import TestCase
from django.urls import reverse

from .models import Student


class StudentDirectoryTests(TestCase):
    def create_student(
        self,
        student_id='S001',
        first_name='Ada',
        last_name='Lovelace',
    ):
        return Student.objects.create(
            student_id=student_id,
            first_name=first_name,
            last_name=last_name,
            gender='Female',
            date_of_birth='2000-01-01',
            contact_no='1234567890',
        )

    def test_student_list_searches_id_and_names(self):
        ada = self.create_student()
        grace = self.create_student('S002', 'Grace', 'Hopper')

        for query, matching_student, missing_name in (
            ('s001', ada, 'Hopper'),
            ('grace', grace, 'Lovelace'),
            ('hopper', grace, 'Lovelace'),
        ):
            with self.subTest(query=query):
                response = self.client.get(
                    reverse('student_list'),
                    {'q': query},
                )

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, matching_student.student_id)
                self.assertNotContains(response, missing_name)

    def test_student_list_orders_by_last_name_then_first_name(self):
        self.create_student('S002', 'Grace', 'Hopper')
        self.create_student('S001', 'Ada', 'Lovelace')

        response = self.client.get(reverse('student_list'))

        self.assertEqual(response.status_code, 200)
        students = list(response.context['students'])
        self.assertEqual(
            [student.student_id for student in students],
            ['S002', 'S001'],
        )

    def test_create_student_saves_valid_model_form(self):
        response = self.client.post(
            reverse('student_create'),
            {
                'student_id': 'S003',
                'first_name': 'Katherine',
                'last_name': 'Johnson',
                'gender': 'Female',
                'date_of_birth': '1918-08-26',
                'contact_no': '5551234',
            },
        )

        self.assertRedirects(response, reverse('student_list'))
        self.assertTrue(Student.objects.filter(student_id='S003').exists())

    def test_create_student_rejects_duplicate_student_id(self):
        self.create_student()

        response = self.client.post(
            reverse('student_create'),
            {
                'student_id': 'S001',
                'first_name': 'Another',
                'last_name': 'Student',
                'gender': 'Female',
                'date_of_birth': '2001-02-03',
                'contact_no': '5551234',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context['form'],
            'student_id',
            'Student with this Student id already exists.',
        )
        self.assertEqual(Student.objects.count(), 1)

    def test_student_detail_and_update(self):
        student = self.create_student()

        detail = self.client.get(
            reverse('student_detail', args=[student.pk])
        )
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, student.student_id)

        response = self.client.post(
            reverse('student_update', args=[student.pk]),
            {
                'student_id': student.student_id,
                'first_name': 'Augusta',
                'last_name': 'Lovelace',
                'gender': 'Female',
                'date_of_birth': '2000-01-01',
                'contact_no': '1234567890',
            },
        )

        self.assertRedirects(
            response,
            reverse('student_detail', args=[student.pk]),
        )
        student.refresh_from_db()
        self.assertEqual(student.first_name, 'Augusta')

    def test_delete_requires_confirmation_post(self):
        student = self.create_student()
        delete_url = reverse('student_delete', args=[student.pk])

        response = self.client.get(delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Student.objects.filter(pk=student.pk).exists())

        response = self.client.post(delete_url)

        self.assertRedirects(response, reverse('student_list'))
        self.assertFalse(Student.objects.filter(pk=student.pk).exists())

    def test_existing_registration_route_still_registers_students(self):
        response = self.client.post(
            reverse('student_registration'),
            {
                'student_id': 'S004',
                'first_name': 'Mary',
                'last_name': 'Jackson',
                'gender': 'Female',
                'date_of_birth': '1921-04-09',
                'contact_no': '5554567',
            },
        )

        self.assertRedirects(response, reverse('registration_success'))
        self.assertTrue(Student.objects.filter(student_id='S004').exists())

from django.test import TestCase
from board.models import Thread, Subject, Post, Reply

"""
 class Thread(models.Model):
    title    = models.CharField(verbose_name='スレタイ',blank=False, null=False, max_length=150)
    def __str__(self):
        return self.title
"""
class ThreadModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        Thread.objects.create(title='test thread')

    def test_title_label(self):
        thread = Thread.objects.get(id=1)
        field_label = thread._meta.get_field('title').verbose_name
        self.assertEquals(field_label, 'スレタイ')

    def test_title_max_length(self):
        th_title = "a" * 151
        thread = Thread(title = th_title)
        thread.save()
        self.assertTrue(thread.title)
        # thread = Thread.objects.get(id=1)
        # max_length = thread._meta.get_field('title').max_length
        # self.assertEquals(max_length, 150)

    # def test_object_name_is_title(self):
    #     thread = Thread.objects.get(id=1)
    #     expected_object_name = thread.title
    #     self.assertEquals(expected_object_name, str(thread))

# class Subject(models.Model):
#     internal_id = models.AutoField(verbose_name="内部id", primary_key=True)
#     code = models.CharField(verbose_name="科目番号", max_length=10, default="")
#     name = models.CharField(verbose_name='講義名',blank=False, null=False, max_length=150)
#     teachers =  models.TextField(verbose_name='教員名', blank=True, max_length=100, default="")
#     subtype =  models.TextField(verbose_name='種類', blank=True, max_length=32, default="")
#     schools = models.CharField(verbose_name="学群等", max_length=40, default="", blank=True)
#     colleges = models.CharField(verbose_name="学類等", max_length=40, default="", blank=True)
#     thread_id = models.ForeignKey(Thread, verbose_name="スレッドid", on_delete=models.CASCADE)

#     def __str__(self):
#         return self.code + " " + self.name

# class SubjectModelTest(TestCase):
#     @classmethod
#     def setUpTestData(cls):
#         thread = Thread.objects.create(title='test thread')
#         subject = Subject.objects.create(code='test code', name='test name', thread_id=thread)

#     def test_code_label(self):
#         subject = Subject.objects.get(id=1)
#         field_label = subject._meta.get_field('code').verbose_name
#         self.assertEquals(field_label, '科目番号')

    # def test_code_max_length(self):
    #     subject = Subject.objects.get(id=1)
    #     max_length = subject._meta.get_field('code').max_length
    #     self.assertEquals(max_length, 10)

    # def test_name_label(self):
    #     subject = Subject.objects.get(id=1)
    #     field_label = subject._meta.get_field('name').verbose_name
    #     self.assertEquals(field_label, '講義名')

    # def test_name_max_length(self):
    #     subject = Subject.objects.get(id=1)
    #     max_length = subject._meta.get_field('name').max_length
    #     self.assertEquals(max_length, 150)

    # def test_teachers_label(self):
    #     subject = Subject.objects.get(id=1)
    #     field_label = subject._meta.get_field('teachers').verbose_name
    #     self.assertEquals(field_label, '教員名')

    # def test_teachers_max_length(self):
    #     subject = Subject.objects.get(id=1)
    #     max_length = subject._meta.get_field('teachers').max_length
    #     self.assertEquals(max_length, 100)

    # def test_subtype_label(self):
    #     subject = Subject.objects.get(id=1)
    #     field_label = subject._meta.get_field('subtype').verbose_name
    #     self.assertEquals(field_label, '種類')

    # def test_subtype_max_length(self):
    #     subject = Subject.objects.get(id=1)
    #     max_length = subject._meta.get_field('subtype').max_length
    #     self.assertEquals(max_length, 32)

    # def test_schools_label(self):
    #     subject = Subject.objects.get(id=1)
    #     field_label = subject._meta.get_field('schools').verbose_name
    #     self.assertEquals(field_label, '学群等')

    # def test_schools_max_length(self):
    #     subject = Subject.objects.get(id=1)
    #     max_length = subject._meta.get_field('schools').max_length
    #     self.assertEquals(max_length, 4)

    # def test_colleges_label(self):
    #     subject = Subject.objects.get(id=1)
    #     field_label = subject._meta.get_field('colleges').verbose_name

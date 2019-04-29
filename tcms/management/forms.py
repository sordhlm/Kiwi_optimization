# -*- coding: utf-8 -*-

from django import forms

from tcms.management.models import Version, Product, Component


class VersionForm(forms.ModelForm):
    class Meta:
        model = Version
        fields = ['product', 'value']

class FeaturesForm(forms.Form):
    product = forms.ModelChoiceField(
        label="Product",
        queryset=Product.objects.all(),
        empty_label=None,
    )
    component = forms.ModelMultipleChoiceField(
        label="Components",
        queryset=Component.objects.none(),
        required=False,
    )
    def populate(self, product_id=None):
        if product_id:
            self.fields['component'].queryset = Component.objects.filter(
                product__id=product_id)
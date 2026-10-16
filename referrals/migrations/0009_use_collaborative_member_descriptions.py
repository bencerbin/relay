from django.db import migrations


MEMBER_DESCRIPTIONS = {
    "American Heart Association": "The American Heart Association is a large non-profit organization that specializes in fundraising cardiovascular research and physical fitness education. They provide comprehensive resources on healthy eating and habits in an effort to prevent heart-related illness. Furthermore, they offer a robust, nationwide CPR-training program and school programs.",
    "Boys & Girls Club of Stamford": "The Boys & Girls Club of Stamford is a dedicated youth facility that offers after-school and enrichment programs for over 1600 children (K-12). Between its STEM programming, 5th Quarter emotional intelligence program, and numerous career-prep programs, The Boys & Girls Club of Stamford is a significant mentor in the",
    "Charter Oak Communities": "Charter Oak Communities is a housing authority that provides affordable and equitable housing to residents of all income levels. Home to a diverse population of over 6000 current residents and 800 families, Charter Oak’s 21 properties offer a safe, family-friendly community to all income levels.",
    "Chartwells": "Chartwells is a food and dining services company contracted by Stamford Public Schools that prioritizes equitable access to healthy food. Their website offers information on free school lunch and further food assistance, including Filling-in-the-Blanks and SNAP.",
    "Chelsea Piers Athletic Club": "Chelsea Piers is an athletic club offering a large variety of sports facilities, programming, and education. The club also offers a well-reputed Daycare and Preschool program. Scholarships are available through the Chelsea Piers Foundation.",
    "Childcare Learning Centers": "Children’s Learning Centers is a non-profit early childhood education provider and the second largest early childhood educator in Connecticut. With curriculum and programming made in collaboration with Yale developmental researchers, CLC empowers children to get a head start in their social and emotional development.",
    "Community Health Center": "Community Health Center is a community based health organization that offers medical, dental, behavioral, and school-based healthcare, with the latter being supplemented by CHC’s two Child Guidance Centers in Stamford. Insurance assistance and Good Faith estimates are available on their website.",
    "Connecticut Foodshare": "As a member of Feeding America and one of Connecticut’s largest food banks, Connecticut Foodshare supports individuals and families by not only distributing food, but addressing root causes and forming long term solutions. Their website contains a mobile pantry locator, SNAP applications, and nutritious recipes.",
    "Fairgate Farm": "Fairgate Farm provides locally-grown produce to Stamford residents regardless of their income level. With a committed volunteer staff and pay-what-you-can model, Fairgate Farm has distributed over 30,000 pounds of fresh produce to the Stamford area, increasing food security and eliminating food deserts in our community. They have also provided hundreds of volunteer and educational opportunities for local residents.",
    "Family Centers": "Family Centers is a nonprofit organization offering education, health, and human services to children, adults and families in Fairfield County. Along with traditional healthcare, they provide a variety of mental health, career-growth, and educational programs for parents and children alike.",
    "Ferguson Library": "The Ferguson Library is located in Public Park Plaza and offers numerous workshops and educational resources for the Stamford community. Along with traditional library services, the Ferguson Library offers passport renewal services and a robust database of local resources including (but not limited to) healthcare, transportation, and food/career assistance.",
    "KIDS’ FANS": "KIDS’ FANS is a Stamford Health program designed to promote childhood wellness, obesity prevention, and physical activity. Through their evidence-based curriculum, KIDS’ FANS has partnered with over 40 community sites to empower children to form healthy nutritional habits. Their website offers an updated brochure on nutritional guidelines and information on pediatric counseling.",
    "Medical Home Initiative": "The Medical Home Initiative serves at-risk and special needs children in their physical, developmental, behavioral or emotional needs. Working with residents of Southwestern Connecticut aged 0-21, the Medical Home Initiative’s Care Coordinators will work closely with you and your child in finding special needs resources including, but not limited to, summer camps, after-school programs, and the 211 Infoline.",
    "Mill River Park Collaborative": "The Mill River Park Collaborative is a non-profit park conservancy that works in a public-private partnership with donors and the City of Stamford to maintain Mill River park--Stamford’s own “Central Park”. The Collaborative offers a variety of on-site community programs such as day camps, after-school programs, and ecological workshops. The Park also offers rental space for birthday parties, barbecues, and weddings!",
    "Optimus Healthcare": "Optimus Healthcare is a non-profit, patient-centered medical home that offers primary, pediatric, behavioral, reproductive, and dental healthcare, particularly for uninsured and underserved patients. Their website includes program details, Optimus locations, and patient forms, including resources on financial assistance and counseling.",
    "ShopRite Supermarket": "ShopRite of Stamford, Commerce Street, Hope Street, and nine other Connecticut ShopRite locations are owned and operated by the Cingari Family, who work closely with the Food Bank of Lower Fairfield to provide food assistance to the residents of Lower Fairfield County. The ShopRite website provides guidance for ordering groceries with SNAP benefits",
    "Saint Joseph Parenting Center": "The Saint Joseph Parenting center is a nonsectarian, primary prevention nonprofit that provides parental education, case management, and community resource support. Their website provides information on their class offerings and volunteer opportunities",
    "Stamford Health": "The Stamford Health Medical Group offers access to more than 150 expert providers across 40 locations. Their website offers a “Find a Doctor” feature to match patients to practitioners based on specialty and zip-code. Patients can also find a comprehensive list of Stamford Health’s medical services, classes, and easily make an appointment.",
    "Stamford Public Schools": "The Stamford Public School District website offers information on the numerous resources provided by the district, including (but not limited to) LGBTQ+, mental health, homelessness, food assistance, transportation, and technology resources. Parents and students can also find any information regarding registration and upcoming holidays or events on the website.",
    "Stamford Public Education Foundation": "The Stamford Public Education foundation is a non-profit that provides the necessary resources and guidance for Stamford students to thrive academically, socially, and emotionally. SPEF offers mentorship programs for all members of the SPEF family, be they student or parent. Their website also includes information on upcoming events, fundraisers, and scholarship or volunteer opportunities.",
    "Stamford Recreation": "The Stamford Recreation website includes information on permits, youth camps and education--including pre-school and after school programs--swimming lessons, and sports leagues. Moreover, a comprehensive map of parks and beaches can be found on the site.",
    "United Way of Coastal and Western Connecticut": "United Way of Coastal and Western Connecticut is a social services organization that helps members of the ALICE® population (Asset Limited, Income Constrained, Employed) address critical needs and gain financial stability. They partner with many local advocacy and non-profit groups and offer a wealth of free resources throughout Lower Fairfield County on their website, along with immigrants rights and LGBTQ+ rights resources.",
    "Women Infant Child Program": "Connecticut’s Women Infant Child Program provides supplemental foods, health care referrals, nutrition education, and breastfeeding promotion and support to low-income pregnant or postpartum women, as well as nutritionally at-risk infants up to age five. Their website offers links to food assistance, housing & rent assistance, electric & utilities assistance, and government grants. Once enrolled in the program, members are entitled to meetings with a nutritionist, health care referrals, and an eWIC card for buying healthy food.",
}


def update_member_descriptions(apps, schema_editor):
    CommunityResource = apps.get_model("referrals", "CommunityResource")

    for name, description in MEMBER_DESCRIPTIONS.items():
        CommunityResource.objects.filter(name=name).update(
            description=description,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("referrals", "0008_add_snap_tag_to_wic"),
    ]

    operations = [
        migrations.RunPython(
            update_member_descriptions,
            migrations.RunPython.noop,
        ),
    ]

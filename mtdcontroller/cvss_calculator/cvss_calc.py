from math import pow, floor

cvss_metrics = {'AV:N': 0.85,
                'AV:A': 0.62,
                'AV:L': 0.55,
                'AV:P': 0.2,
                'AC:L': 0.77,
                'AC:H': 0.44,
                'PR:N': 0.85,
                'PR:L': 0.62,
                'PR:H': 0.27,
                'UI:N': 0.85,
                'UI:R': 0.62,
                'C:H': 0.56,
                'C:L': 0.22,
                'C:N': 0,
                'I:H': 0.56,
                'I:L': 0.22,
                'I:N': 0,
                'A:H': 0.56,
                'A:L': 0.22,
                'A:N': 0,
                }


def cvss2to3(cvss_vector):
    splitted_vector = cvss_vector.split('/')
    for i in range(len(splitted_vector)):
        if 'Au:' in splitted_vector[i]:
            splitted_vector[i] = splitted_vector[i].replace('Au:', 'PR:')
            if ':S' in splitted_vector[i]:
                splitted_vector[i] = splitted_vector[i].replace(':S', ':L')
            elif ':M' in splitted_vector[i]:
                splitted_vector[i] = splitted_vector[i].replace(':M',':H')
        elif 'C:' in splitted_vector[i] or 'I:' in splitted_vector[i] or 'A:' in splitted_vector[i]:
            splitted_vector[i] = splitted_vector[i].replace(':P', ':L')
            splitted_vector[i] = splitted_vector[i].replace(':C', ':H')
        elif 'AC:' in splitted_vector[i]:
            if ':M' in splitted_vector[i]:
                splitted_vector[i] = 'AC:H'
                splitted_vector.append('UI:R')
            if ':H' in splitted_vector[i]:
                splitted_vector[i] = 'AC:H'
                splitted_vector.append('UI:R')
            else:
                splitted_vector.append('UI:N')
    if '/C:C' in cvss_vector and '/I:C' in cvss_vector and '/A:C' in cvss_vector:
        splitted_vector.append('S:C')
    else:
        splitted_vector.append('S:U')
    return 'CVSS:3.1/' + '/'.join(splitted_vector)


def exploitability_score(cvss_vector):
    # formula from https://www.first.org/cvss/v3.1/specification-document
    # expl = 8.22 x AV x AC x PR x UI
    if 'CVSS' not in cvss_vector or 'CVSS:2' in cvss_vector:
        # convert cvss vector to v3.1 layout following https://security.stackexchange.com/questions/127335/how-to-convert-risk-scores-cvssv1-cvssv2-cvssv3-owasp-risk-severity
        cvss_vector = cvss2to3(cvss_vector)
    splitted_vector = cvss_vector.split('/')
    expl = 8.22
    for metric in splitted_vector:
        if 'AV' in metric:
            expl *= cvss_metrics[metric]
        elif 'AC' in metric:
            expl *= cvss_metrics[metric]
        elif 'PR' in metric:
            expl *= cvss_metrics[metric]
        elif 'UI' in metric:
            expl *= cvss_metrics[metric]
    return expl


def roundup(n):
    multiplier = round(n*1000)
    if (multiplier % 100) == 0:
        return multiplier /1000.0
    else:
        return (floor(multiplier/100)+1)/10.0


def scores(cvss_vector):
    # formula from https://www.first.org/cvss/v3.1/specification-document
    splitted_vector = cvss_vector.split('/')
    if 'CVSS' not in cvss_vector or 'CVSS:2' in cvss_vector:
        # convert cvss vector to v3.1 layout following https://security.stackexchange.com/questions/127335/how-to-convert-risk-scores-cvssv1-cvssv2-cvssv3-owasp-risk-severity
        cvss_vector = cvss2to3(cvss_vector)
    splitted_vector = cvss_vector.split('/')
    for metric in splitted_vector:
        if 'C:' in metric:
            c = cvss_metrics[metric]
        elif 'I:' in metric:
            i = cvss_metrics[metric]
        elif 'A:' in metric:
            a = cvss_metrics[metric]
    # ISS =	1 - [ (1 - Confidentiality) × (1 - Integrity) × (1 - Availability) ]
    iss = 1 - ( (1-c)*(1-i)*(1-a) )
    # Impact = # If Scope is Unchanged
    #                   6.42 × ISS
    #            If Scope is Changed
    #                   7.52 × (ISS - 0.029) - 3.25 × (ISS - 0.02)^15
    if 'S:U' in cvss_vector:
        scope= 'u'
        impact = 6.42 * iss
    else:
        scope= 'c'
        impact = 7.52 * (iss - 0.029) - 3.25 * pow((iss - 0.02), 15)

    exploitability = exploitability_score(cvss_vector)
    if impact <= 0:
        return 0, exploitability
    else:
        if scope == 'u':
            score = min(impact + exploitability, 10)
        else:
            score = min( 1.08*(impact + exploitability), 10)
        return roundup(score), exploitability


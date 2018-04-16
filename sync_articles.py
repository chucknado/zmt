import arrow

from helpers import read_data, write_data, get_settings, package_article, get_resource_list, \
    post_resource, put_resource, write_js_redirects


settings = get_settings()
src_root = settings['src_root']
dst_root = settings['dst_root']
locale = settings['locale']
sync_dates = read_data('sync_dates')
last_sync = arrow.get(sync_dates['articles'])
section_map = read_data('section_map')
article_map = read_data('article_map')
exceptions = read_data('exceptions')

for section in section_map:

    # test-only section (ref docs) -> comment out for sync
    if section != "206223848":
        continue

    dst_section = section_map[section]
    print('\nGetting articles in section {}...'.format(section))
    url = '{}/{}/sections/{}/articles.json'.format(src_root, locale, section)
    articles = get_resource_list(url)
    for src_article in articles:
        if str(src_article['id']) in exceptions:
            print('{} is an exception. Skipping...'.format(src_article['id']))
            continue
        if last_sync < arrow.get(src_article['created_at']):
            print('- adding article {} to destination section {}'.format(src_article['id'], dst_section))
            url = '{}/{}/sections/{}/articles.json'.format(dst_root, locale, dst_section)
            payload = package_article(src_article)
            new_article = post_resource(url, payload)
            article_map[str(src_article['id'])] = new_article['id']
            continue
        if last_sync < arrow.get(src_article['edited_at']):
            print('- updating article {} in destination section {}'.format(src_article['id'], dst_section))
            dst_article = article_map[str(src_article['id'])]
            url = '{}/articles/{}/translations/{}.json'.format(dst_root, dst_article, locale)
            payload = package_article(src_article, put=True)
            updated_translation = put_resource(url, payload)
            continue
        print('- article {} is up-to-date in destination section {}'.format(src_article['id'], dst_section))

utc = arrow.utcnow()
sync_dates['articles'] = utc.format()
write_data(sync_dates, 'sync_dates')
write_data(article_map, 'article_map')
write_js_redirects(article_map)

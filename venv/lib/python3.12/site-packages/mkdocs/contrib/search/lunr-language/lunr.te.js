/*!
 * Lunr languages, `Hindi` language
 * https://github.com/MiKr13/lunr-languages
 *
 * Copyright 2023, India
 * http://www.mozilla.org/MPL/
 */
/*!
 * based on
 * Snowball JavaScript Library v0.3
 * http://code.google.com/p/urim/
 * http://snowball.tartarus.org/
 *
 * Copyright 2010, Oleg Mazko
 * http://www.mozilla.org/MPL/
 */

/**
 * export the module via AMD, CommonJS or as a browser global
 * Export code from https://github.com/umdjs/umd/blob/master/returnExports.js
 */
;
(function(root, factory) {
  if (typeof define === 'function' && define.amd) {
    // AMD. Register as an anonymous module.
    define(factory)
  } else if (typeof exports === 'object') {
    /**
     * Node. Does not work with strict CommonJS, but
     * only CommonJS-like environments that support module.exports,
     * like Node.
     */
    module.exports = factory()
  } else {
    // Browser globals (root is window)
    factory()(root.lunr);
  }
}(this, function() {
  /**
   * Just return a value to define the module export.
   * This example returns an object, but the module
   * can return a function as the exported value.
   */
  return function(lunr) {
    /* throw error if lunr is not yet included */
    if ('undefined' === typeof lunr) {
      throw new Error('Lunr is not present. Please include / require Lunr before this script.');
    }

    /* throw error if lunr stemmer support is not yet included */
    if ('undefined' === typeof lunr.stemmerSupport) {
      throw new Error('Lunr stemmer support is not present. Please include / require Lunr stemmer support before this script.');
    }

    /* register specific locale function */
    lunr.te = function() {
      this.pipeline.reset();
      this.pipeline.add(
        lunr.te.trimmer,
        lunr.te.stopWordFilter,
        lunr.te.stemmer
      );

      // change the tokenizer for japanese one
      // if (isLunr2) { // for lunr version 2.0.0
      //   this.tokenizer = lunr.hi.tokenizer;
      // } else {
      //   if (lunr.tokenizer) { // for lunr version 0.6.0
      //     lunr.tokenizer = lunr.hi.tokenizer;
      //   }
      //   if (this.tokenizerFn) { // for lunr version 0.7.0 -> 1.0.0
      //     this.tokenizerFn = lunr.hi.tokenizer;
      //   }
      // }

      if (this.searchPipeline) {
        this.searchPipeline.reset();
        this.searchPipeline.add(lunr.te.stemmer)
      }
    };

    /* lunr trimmer function */
    lunr.te.wordCharacters = "\u0C00-\u0C04\u0C05-\u0C14\u0C15-\u0C39\u0C3E-\u0C4C\u0C55-\u0C56\u0C58-\u0C5A\u0C60-\u0C61\u0C62-\u0C63\u0C66-\u0C6F\u0C78-\u0C7F\u0C3C\u0C3D\u0C4D\u0C5D\u0C77\u0C64\u0C65";
    lunr.te.trimmer = lunr.trimmerSupport.generateTrimmer(lunr.te.wordCharacters);

    lunr.Pipeline.registerFunction(lunr.te.trimmer, 'trimmer-te');
    /* lunr stop word filter */
    lunr.te.stopWordFilter = lunr.generateStopWordFilter(
      'అందరూ అందుబాటులో అడగండి అడగడం అడ్డంగా అనుగుణంగా అనుమతించు అనుమతిస్తుంది అయితే ఇప్పటికే ఉన్నారు ఎక్కడైనా ఎప్పుడు ఎవరైనా ఎవరో ఏ ఏదైనా ఏమైనప్పటికి ఒక ఒకరు కనిపిస్తాయి కాదు కూడా గా గురించి చుట్టూ చేయగలిగింది తగిన తర్వాత దాదాపు దూరంగా నిజంగా పై ప్రకారం ప్రక్కన మధ్య మరియు మరొక మళ్ళీ మాత్రమే మెచ్చుకో వద్ద వెంట వేరుగా వ్యతిరేకంగా సంబంధం'.split(' '));
    /* lunr stemmer function */
    lunr.te.stemmer = (function() {

      return function(word) {
        // for lunr version 2
        if (typeof word.update === "function") {
          return word.update(function(word) {
            return word;
          })
        } else { // for lunr version <= 1
          return word;
        }

      }
    })();

    var segmenter = lunr.wordcut;
    segmenter.init();
    lunr.te.tokenizer = function(obj) {
      if (!arguments.length || obj == null || obj == undefined) return []
      if (Array.isArray(obj)) return obj.map(function(t) {
        return isLunr2 ? new lunr.Token(t.toLowerCase()) : t.toLowerCase()
      });

      var str = obj.toString().toLowerCase().replace(/^\s+/, '');
      return segmenter.cut(str).split('|');
    }

    lunr.Pipeline.registerFunction(lunr.te.stemmer, 'stemmer-te');
    lunr.Pipeline.registerFunction(lunr.te.stopWordFilter, 'stopWordFilter-te');

  };
}))